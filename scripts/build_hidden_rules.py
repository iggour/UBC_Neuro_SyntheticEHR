#!/usr/bin/env python3
"""
build_hidden_rules.py  (distillation, all scenarios, step 1: leak / unlock rules from the role cards)

For s3 the words that decide "did a hidden item come out too early?" were written by hand
(UNLOCK, PRIVATE, ASKED in make_conversations.py; EARLY in measure_teacher.py; LEAK in run_probes.py).
This script drafts the same kind of rules for any scenario from its role card, so the other 14
scenarios can be generated, filtered and tested the same way. v2 (2026-11-18), after the first
comparison with the hand-written s3 rules (compare_hidden_rules.py).

Three parts:
  1. Read from the card with fixed code (no model):
       who is in the room (patient and companion; "others" such as a son on speakerphone are not),
       who must be out of the room before an item may come out ("while her mother is out of the room",
       "sees Anna alone"), conditions that words cannot check ("AFTER the diagnosis has been given",
       "with Mark's agreement"), and quoted lines in behaviour_rules: lines for "before ... disclosed" /
       "never disclose" situations may be said at any time; lines for "after X has been disclosed" are
       disclosures of X and become held-out tests.
  2. Teacher call 1, tests only: for each item, who reveals it, and 6 disclosures, 6 safe replies,
       6 unlock questions and 6 near-miss questions.
  3. Teacher call 2, phrases only (it does not see the tests): leak, leak_extra, unlock, asked.
     The tests are split in two halves. Failures on the first half (dev) are sent back to the teacher,
     up to --tries times; the second half (held out, plus the tests from the card) is never shown to
     the teacher and is reported separately, as an honest check.

Fields:
  speaker      who reveals the item. For a companion's item, leak words count only in that person's
               lines ("Luis: ..."); for the patient's items, anywhere in the reply.
  leak         words that can only mean the item came out (probes; early-disclosure check)
  leak_from_card  lines the behaviour rules give for after the item is disclosed ("haven't counted"), added
               to leak by fixed code
  leak_extra   wider words worth a look (leak + leak_extra = the broad check, like EARLY)
  unlock       trainee words that meet disclose_when (topic only)
  asked        (private items only) a direct question about the item; a plain "yes" to it counts. At run
               time (load_rules) the patient's name for she/he and the unlock phrases that are not one
               short word are added.

Phrase syntax (case does not matter; whole words):
    suicid*            * at the end of a word = any ending (suicide, suicidal)
    end [my|her] life  [a|b] = either word
    kept ... tablets   ... = both parts in the same sentence, at most 40 characters apart
A leak or leak_extra phrase that is a single word needs at least 6 letters (no "tired").

Self-tests:
    leak     matches every disclosure (in the speaker's lines); matches no safe reply
    leak, leak_extra   match nothing that may be said at any time (trainee brief, opening line, facts,
             personality, companion stance, allowed lines of every item, before/never lines of the rules)
    unlock   matches every unlock question and no near-miss question (unlock and asked accept other
             word endings: "kill yourself" also matches "killing yourself")
    asked    (private items) matches at least one unlock question and no near-miss question

Usage:
    python3 scripts/build_hidden_rules.py s3                  one scenario (calls the teacher twice or more)
    python3 scripts/build_hidden_rules.py all                 all 15
    python3 scripts/build_hidden_rules.py all --plan          part 1 only: what was read from the cards
    python3 scripts/build_hidden_rules.py s3 --prompt         print the first prompt that would be sent
    python3 scripts/build_hidden_rules.py s3 --draft d.json   phrases (and tests) written elsewhere (no teacher)
    python3 scripts/build_hidden_rules.py s3 --test-only      re-run the self-tests after editing the file

Writes evaluation/hidden_rules/<short>.yaml (Reviewed by: PENDING), <short>_teacher_log.json and summary.md.
Short names: the part of the scenario folder name before the first "_" (s1, s2, s3, A1, ..., C4-1, ..., C5-3).
Other scripts read a file with load_rules(short). s3 keeps its hand-written rules for now.
"""
import argparse, datetime, json, pathlib, re, sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "evaluation" / "hidden_rules"
GAP = r"[^.?!\n]{0,40}?"
N_TESTS = 6          # asked of the teacher per test kind; at least MIN_TESTS must come back
MIN_TESTS = 4
KINDS = ("disclosures", "safe_replies", "unlock_questions", "near_miss_questions")


# ---------------------------------------------------------------- phrases -> regular expressions

def _lit(text):
    out, space = [], False
    for ch in text:
        if ch.isspace():
            if not space:
                out.append(r"\s+")
            space = True
            continue
        space = False
        if ch == "*":
            out.append(r"\w*")
        elif ch in "'’":
            out.append("['’]")
        else:
            out.append(re.escape(ch))
    return "".join(out)


def stem(w):
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[:-len(suf)]
    return w


def loosen(p):
    """Trainee-side phrases accept other word endings: "kill yourself" also matches "killing yourself",
    "any plans" also "any plan". Words of 3+ letters get any ending; short words stay as they are."""
    return re.sub(r"(?<![\w'*])([a-z]{3,})(?![\w'*])", lambda m: stem(m.group(1)) + "*", p)


def phrase_regex(phrase, loose=False):
    """One phrase in the syntax above -> a regular expression (string). loose: see loosen()."""
    p = " ".join(str(phrase).lower().split())
    if loose:
        p = loosen(p)
    parts = [x.strip() for x in p.split("...")]
    if len(re.sub(r"[\s.*\[\]|]", "", p)) < 3 or not all(parts):
        raise ValueError(f"phrase too short or with an empty part: {phrase!r}")
    bad = sorted(set(re.findall(r"[?+(){}\\^$]", p)))
    if bad:
        raise ValueError(f"regular-expression characters {''.join(bad)} in {phrase!r}; use the phrase syntax")
    bodies = []
    for part in parts:
        s = ""
        for tok in re.split(r"(\[[^\]]*\])", part):
            if tok.startswith("[") and tok.endswith("]"):
                opts = [o.strip() for o in tok[1:-1].split("|")]
                if not all(opts):
                    raise ValueError(f"empty choice in {phrase!r}")
                s += "(?:" + "|".join(_lit(o) for o in opts) + ")"
            elif "[" in tok or "]" in tok:
                raise ValueError(f"unmatched bracket in {phrase!r}")
            else:
                s += _lit(tok)
        bodies.append(s)
    return r"(?<!\w)" + GAP.join(bodies) + r"(?!\w)"


def too_common(phrase):
    """A leak phrase that is one short word ("tired") flags far too much."""
    p = str(phrase).strip()
    return " " not in p and "..." not in p and "[" not in p and len(p.rstrip("*")) < 6


def regex_of(phrases, loose=False):
    """A phrase list -> one pattern string, or None for an empty list."""
    ps = [phrase_regex(p, loose) for p in phrases or []]
    return "|".join(f"(?:{x})" for x in ps) if ps else None


def label_re(name):
    return rf"^[*_ ]*{re.escape(name)}\b[^:\n]{{0,25}}:"


def item_regex(phrases, speaker, patient):
    """Pattern for an item's leak words. A companion's item counts only in that person's lines."""
    pat = regex_of(phrases)
    if pat and speaker and speaker != patient:
        return rf"(?m){label_re(speaker)}[^\n]*?(?:{pat})"
    return pat


def matches(phrases, text, loose=False):
    """The phrases in the list that match the text."""
    t = str(text).replace("’", "'")
    return [p for p in phrases or [] if re.search(phrase_regex(p, loose), t, re.I)]


def speaker_matches(phrases, text, speaker, patient):
    """As matches(), but for a companion's item only that person's lines are searched."""
    if speaker and speaker != patient:
        text = "\n".join(re.findall(label_re(speaker) + r"(.*)$", str(text), re.M | re.I))
    return matches(phrases, text)


def runtime_asked(it, patient):
    """Questions whose plain "yes" counts as a disclosure (private items): the teacher's asked phrases, the
    same with the patient's first name for she/he ("has she" -> "has Teresa"), and the unlock phrases that
    are not one short word (a "yes" after "plan" may be agreeing to a safety plan)."""
    asked = it.get("asked") or []
    if not it.get("private_because"):
        return asked
    named = [re.sub(r"\b(?:she|he)\b", patient, p) for p in asked if patient and re.search(r"\b(?:she|he)\b", p)]
    return asked + named + [p for p in it.get("unlock") or [] if not too_common(p)]


def load_rules(short):
    """Rules from evaluation/hidden_rules/<short>.yaml in the shapes the s3 code uses:
    unlock / asked / leak / early: {item_id: pattern}; private: [{"person": first name, "items": [ids]}].
    None if the file does not exist."""
    f = OUT / f"{short}.yaml"
    if not f.exists():
        return None
    d = yaml.safe_load(f.read_text(encoding="utf-8"))
    patient = d.get("patient")
    r = {"unlock": {}, "asked": {}, "leak": {}, "early": {}, "private": []}
    priv = {}
    for it in d["items"]:
        i, sp = it["id"], it.get("speaker")
        leak = (it.get("leak") or []) + (it.get("leak_from_card") or [])
        for key, pat in (("leak", item_regex(leak, sp, patient)),
                         ("early", item_regex(leak + (it.get("leak_extra") or []), sp, patient)),
                         ("unlock", regex_of(it.get("unlock"), True)), ("asked", regex_of(runtime_asked(it, patient), True))):
            if pat:
                r[key][i] = pat
        for person in it.get("private_from") or []:
            priv.setdefault(person, []).append(i)
    r["private"] = [{"person": p, "items": v} for p, v in priv.items()]
    return r


# ---------------------------------------------------------------- part 1: read the card (no model)

def scenario_dirs():
    return sorted(d for d in (ROOT / "scenarios").iterdir() if (d / "role_card.yaml").exists())


def short_of(sid):
    return sid.split("_")[0]


def as_list(x):
    return x if isinstance(x, list) else [x] if x else []


def leave_text(v):
    if v is True or (isinstance(v, str) and v.lower().startswith("yes")):
        return "yes"
    if v is False or (isinstance(v, str) and v.lower().startswith("no")):
        return "no"
    return "not stated"


def people(card):
    out = [{"name": card["persona"]["name"], "role": "patient", "relation": "patient", "in_room": True}]
    for c in as_list(card.get("companion")):
        out.append({"name": c["name"], "role": "companion", "relation": str(c.get("relation", "")),
                    "stance": c.get("stance"), "in_room": True, "will_leave_room": leave_text(c.get("will_leave_room"))})
    for o in as_list(card.get("others")):
        out.append({"name": o["name"], "role": "other", "relation": str(o.get("relation", "")),
                    "stance": o.get("stance"), "in_room": False})
    for p in out:
        p["first"] = str(p["name"]).split()[0]
    return out


STOP = {"her", "his", "their", "the", "a", "an", "is", "are"}


def resolve(words, ppl):
    """Names in a clause such as "her mother" or "Luis" -> first names of people in the room."""
    w = words.lower()
    room = [p for p in ppl if p["in_room"]]
    hit = [p["first"] for p in room if re.search(rf"\b{re.escape(p['first'].lower())}\b", w)]
    if not hit:
        keys = [x for x in re.findall(r"[a-z]+", w) if x not in STOP]
        hit = [p["first"] for p in room if p["role"] == "companion"
               and any(re.search(rf"\b{k}\b", p["relation"].lower()) for k in keys)]
    return hit


def private_rule(dw, ppl):
    """(people who must be out of the room, the clause that says so), or ([], None)."""
    m = re.search(r"while ([A-Za-z' ]+?) (?:is|are) out of the room", dw)
    if m:
        return resolve(m.group(1), ppl), m.group(0)
    m = re.search(r"\b(?:sees?|speaks? with|speaking with|talks? (?:to|with)) ([A-Z]\w+) alone\b", dw)
    if m and not re.search(r"\bor\b", dw):        # "..., or asks Anna directly" = an alternative, not a must
        target = resolve(m.group(1), ppl)
        return [p["first"] for p in ppl if p["in_room"] and p["first"] not in target], m.group(0)
    return [], None


def word_free_conditions(dw):
    """Parts of disclose_when that the word rules cannot check (kept for the judge and for review)."""
    notes = re.findall(r"\b(?:AFTER|after) [^,.;)]+", dw)
    notes += re.findall(r"with \w+'s (?:agreement|knowledge|consent)", dw)
    return [" ".join(n.split()) for n in notes]


def rule_lines(card):
    """Quoted lines in behaviour_rules that name hidden items:
    ({item_id: [lines said only after it was disclosed]}, [lines that may be said at any time])."""
    ids = [h["id"] for h in card.get("hidden", [])]
    after, anytime = {}, []
    for rule in card.get("behaviour_rules", []):
        for sent in re.split(r"(?<=[.!?])\s+(?=[A-Z])", " ".join(str(rule).split())):
            named = [i for i in ids if re.search(rf"\b(?:{re.escape(i)}|{re.escape(i.split('_')[0])})\b", sent)]
            quotes = re.findall(r'"([^"]{3,})"', sent)
            if not named or not quotes:
                continue
            if re.search(r"\bafter\b[^.]*\b(?:has|have) been disclosed", sent, re.I):
                for i in named:
                    after.setdefault(i, []).extend(quotes)
            elif re.search(r"\bbefore\b|\bnever disclose|\bdo not (?:reveal|confirm|disclose)", sent, re.I):
                anytime += quotes
    return after, anytime


def card_leak_phrases(lines):
    """Lines the card says come only after an item is disclosed -> leak phrases: each clause with a word of
    6+ letters, without a leading "I" ("I don't know, I haven't counted." -> "haven't counted")."""
    out = []
    for line in lines:
        for cl in re.split(r"[,.;!?]", line):
            cl = re.sub(r"^\s*I\s+", "", cl.strip())
            if len(cl.split()) >= 2 and any(len(w.replace("'", "")) >= 6 for w in cl.split()):
                out.append(cl)
    return out


def flat(x):
    if isinstance(x, dict):
        return [s for v in x.values() for s in flat(v)]
    if isinstance(x, list):
        return [s for v in x for s in flat(v)]
    return [str(x)] if x not in (None, "") else []


def allowed_texts(card, ppl, anytime):
    """Text that may be said at any time: no leak or leak_extra phrase may match it."""
    sc, pe = card.get("scenario", {}), card["persona"]
    out = [("trainee brief", " ".join(str(sc.get("trainee_brief", "")).split())),
           ("opening line", str(pe.get("opening_line", ""))),
           ("personality", " ".join(str(pe.get("personality", "")).split())),
           ("emotional baseline", str(pe.get("emotional_baseline", "")))]
    out += [(f"{p['first']}'s stance", str(p["stance"])) for p in ppl if p.get("stance")]
    out += [("facts", s) for s in flat(card.get("facts")) + flat(card.get("family_canonical"))]
    out += [(f"{h['id']} {k}", str(v)) for h in card.get("hidden", []) for k, v in h.items()
            if k == "partial_before" or k.startswith("if_")]
    out += [("behaviour rule line", q) for q in anytime]
    return [(k, v) for k, v in out if v.strip() and v != "None"]


def plan(sid):
    card = yaml.safe_load((ROOT / "scenarios" / sid / "role_card.yaml").read_text(encoding="utf-8"))
    ppl = people(card)
    after, anytime = rule_lines(card)
    allowed = allowed_texts(card, ppl, anytime)
    items = []
    for h in card.get("hidden", []):
        dw = " ".join(str(h.get("disclose_when", "")).split())
        who, why = private_rule(dw, ppl)
        items.append({"id": h["id"], "disclose_when": dw, "private_from": who, "private_because": why,
                      "not_checked_by_words": word_free_conditions(dw), "allowed": allowed,
                      "card_tests": {"disclosures": after.get(h["id"], [])},
                      "leak_from_card": card_leak_phrases(after.get(h["id"], [])), "card_item": h})
    return {"sid": sid, "short": short_of(sid), "card": card, "people": ppl, "patient": ppl[0]["first"],
            "items": items}


def print_plan(pl):
    print(f"\n== {pl['short']} ({pl['sid']})")
    print("   people: " + "; ".join(f"{p['first']} ({p['role']}" + (", not in room" if not p["in_room"] else "")
                                    + (f", leaves: {p['will_leave_room']}" if "will_leave_room" in p else "") + ")"
                                    for p in pl["people"]))
    rl = [a for k, a in pl["items"][0]["allowed"] if k == "behaviour rule line"] if pl["items"] else []
    if rl:
        print(f"   behaviour-rule lines allowed at any time: {rl}")
    for it in pl["items"]:
        line = f"   {it['id']}"
        if it["private_because"]:
            line += f"  PRIVATE from {it['private_from'] or '?? (name not found)'}  [{it['private_because']}]"
        if it["not_checked_by_words"]:
            line += f"  not checked: {it['not_checked_by_words']}"
        if it["card_tests"]["disclosures"]:
            line += f"  disclosure lines from the rules: {it['card_tests']['disclosures']} -> leak {it['leak_from_card']}"
        print(line)


# ---------------------------------------------------------------- parts 2 and 3: the teacher

INTRO = """You help build an automatic checker for a clinical-communication training simulator.
A language model plays a fictional patient and family members. Each person has hidden items: things
they reveal only when the trainee asks in the right way (disclose_when). Word rules will catch a
hidden item coming out too early, and show when the trainee has asked the question that earns it.
"""

TESTS_PROMPT = INTRO + """
Your job now is ONLY the test sentences the word rules will be checked against (someone else writes the
rules). Make them realistic and varied, as the simulator would really produce them.

For EVERY hidden item of the scenario below, write:
  id                   the item id
  speaker              first name of the person who reveals it (one of: @NAMES@)
  disclosures          @N@ replies that give the item away, as the simulator might say them: plain, hesitant
                       ("I... I've had thoughts."), indirect, very short. Use the item's own key words in some
                       and other words in others. If the speaker is the patient, make 2 of them third person,
                       as in an out-of-character summary ("She has been ..."), with no name label. All other
                       replies start with the speaker's first name and a colon ("Name: ...").
  safe_replies         @N@ in-character replies that do NOT give the item away: deflections, the allowed lines,
                       lines the behaviour rules give for other situations, and talk about nearby facts that are
                       not secret. At least 2 must share words with the item but be harmless (for example, about
                       medicines taken as prescribed when the item is about pills that were stopped).
  unlock_questions     @N@ trainee lines that meet disclose_when (topic only: tone, order and who is in the
                       room are checked elsewhere). Include 2 short plain ones.
  near_miss_questions  @N@ trainee lines on a NEARBY topic that do NOT meet disclose_when. Include the nearby
                       topics the card itself separates from this item (in disclose_when or the behaviour rules).
                       Never lines that differ only in tone or kindness.
Add no facts beyond the card. Never write self-harm methods, amounts or doses beyond the item's own content.

Answer with JSON only, no other text:
{"items": [{"id": "...", "speaker": "...", "disclosures": [...], "safe_replies": [...],
"unlock_questions": [...], "near_miss_questions": [...]}]}

The scenario:
@CARD@
"""

EXAMPLE = {"items": [{
    "id": "H1_stopped_pills",
    "leak": ["stopped ... [pills|tablets|medicine*|medication*]", "not [taking|been taking] ... [pills|tablets]",
             "haven't [taken|been taking] ... [pills|tablets]", "[skip|skipped|skipping] ... [pills|tablets|doses]",
             "[she|Joan] ... stopped ... [pills|tablets]", "Tom doesn't know", "don't tell Tom"],
    "leak_extra": ["blood pressure [pills|tablets] ... dizzy", "three weeks ... [pills|tablets]"],
    "unlock": ["[medicine*|medication*|pills|tablets]", "blood pressure", "side effect*"],
    "asked": ["[stopped|skipping|missing] ... [pills|tablets|medicine*|doses]",
              "[taking|take] ... [pills|tablets|medicine*] ... [every day|regularly|as prescribed]"]}]}
EXAMPLE_CARD = ('(Example card: patient Joan Price, 70, with her son Tom. Hidden item H1_stopped_pills, speaker Joan: '
                '"Joan stopped her blood-pressure pills three weeks ago because they made her dizzy. Tom does not '
                'know." disclose_when: "Trainee asks Joan, while Tom is out of the room, an open question about how '
                'her medicines are going." private: true. The brief says she has dizzy spells, so "dizzy" alone '
                'may be said at any time.)')

PHRASES_PROMPT = INTRO + """
Your job now is the word rules. They will be tested on realistic replies and questions you will not see.

Phrase syntax (case does not matter; phrases match whole words):
  suicid*            * at the end of a word = any ending
  end [my|her] life  [a|b] = either word (no empty choices)
  kept ... tablets   ... = both parts in the same sentence, at most 40 characters apart
Plain phrases only: no other symbols.

For EVERY hidden item of the scenario below, write:
  id           the item id (the speaker of each item is given)
  leak         6 to 15 phrases that can only mean the item came out. Include the item's own key words as
               written in its content, the short ways a hesitant speaker gives it away ("I've had thoughts"),
               other wordings, and, for the patient's items, third-person forms (she/he/her/his/the name), as
               in an out-of-character summary. A single-word phrase needs at least 6 letters and must be
               specific to the item. No leak phrase may match anything that may be said at any time: the
               trainee brief, opening line, personality, stances, facts_not_secret, the allowed_lines of any
               item, and lines the behaviour rules give for before an item is disclosed. (Lines the
               behaviour rules give for after an item is disclosed are added by the script.)
  leak_extra   0 to 8 wider phrases worth a human look. Same limits as leak (no single short words, nothing
               that may be said at any time).
  unlock       6 to 15 phrases a trainee would use when asking the question in disclose_when, in many
               wordings, including short ones ("a plan"). Words only check the TOPIC, not tone, order or
               who is in the room. Do not unlock on a nearby topic the card separates from the item.
               The script accepts other word endings by itself ("kill yourself" also matches "killing
               yourself"), so do not list endings; list different words instead.
  asked        only if the item has "private": true: 3 to 8 phrases for a DIRECT question about the item
               itself, so that a plain "yes" to it counts as a disclosure: put to the speaker ("have you ...")
               and put to another family member about the speaker ("has she ...", "has she talked to you
               about ..."). Otherwise [].

Answer with JSON only, no other text. A made-up example (not one of our scenarios):
@EXAMPLE_CARD@
@EXAMPLE@

The scenario:
@CARD@
"""

FIX = """Your rules failed these self-tests (some tests are hidden, so make the phrases general, not fitted
to these sentences):
@FAILS@
Answer with the full corrected JSON for ALL items, phrases only, JSON only."""


def card_view(pl, speakers=None):
    card = pl["card"]
    sc, pe = card.get("scenario", {}), card["persona"]
    items = []
    for it in pl["items"]:
        h = it["card_item"]
        v = {"id": h["id"]}
        if speakers:
            v["speaker"] = speakers.get(h["id"])
        v.update({"content": " ".join(str(h.get("content", "")).split()), "disclose_when": it["disclose_when"],
                  "allowed_lines": {k: str(h[k]) for k in h if k == "partial_before" or k.startswith("if_")},
                  "private": bool(it["private_because"])})
        items.append(v)
    view = {"setting": sc.get("setting"), "trainee_brief": " ".join(str(sc.get("trainee_brief", "")).split()),
            "opening_line": pe.get("opening_line"),
            "patient_personality": " ".join(str(pe.get("personality", "")).split()),
            "people": [{k: p[k] for k in ("name", "role", "relation", "stance", "in_room") if p.get(k) is not None}
                       for p in pl["people"]],
            "facts_not_secret": card.get("facts"), "behaviour_rules": card.get("behaviour_rules"),
            "hidden_items": items}
    return json.dumps(view, indent=1, ensure_ascii=False, default=str)


def tests_prompt(pl):
    return (TESTS_PROMPT.replace("@NAMES@", ", ".join(p["first"] for p in pl["people"]))
            .replace("@N@", str(N_TESTS)).replace("@CARD@", card_view(pl)))


def phrases_prompt(pl, speakers):
    return (PHRASES_PROMPT.replace("@EXAMPLE_CARD@", EXAMPLE_CARD).replace("@EXAMPLE@", json.dumps(EXAMPLE, indent=1))
            .replace("@CARD@", card_view(pl, speakers)))


def parse_json(raw):
    t = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
    a, b = t.find("{"), t.rfind("}")
    if a < 0 or b < a:
        raise ValueError("no JSON object in the answer")
    try:
        return json.loads(t[a:b + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON error: {e}")


def str_list(x):
    return [str(s) for s in x] if isinstance(x, list) else []


def by_id(draft):
    return {str(r.get("id")): r for r in draft.get("items", []) if isinstance(r, dict)} if isinstance(draft, dict) else {}


def split_tests(t, card_tests):
    """Every other sentence goes to dev (shown to the teacher on failure), the rest to held out,
    plus the tests read from the card."""
    dev = {k: str_list(t.get(k))[0::2] for k in KINDS}
    held = {k: str_list(t.get(k))[1::2] + str_list(card_tests.get(k)) for k in KINDS}
    return dev, held


def check_tests(draft, pl):
    """Teacher call 1 -> ({id: (speaker, dev, held)}, problems)."""
    names = [p["first"] for p in pl["people"]]
    got, out, probs = by_id(draft), {}, []
    for it in pl["items"]:
        r = got.get(it["id"])
        if r is None:
            probs.append(f"{it['id']}: missing")
            continue
        sp = str(r.get("speaker", "")).split(" ")[0]
        if sp not in names:
            probs.append(f"{it['id']}: speaker {r.get('speaker')!r} is not one of {names}")
        for k in KINDS:
            if len(str_list(r.get(k))) < MIN_TESTS:
                probs.append(f"{it['id']}: fewer than {MIN_TESTS} {k}")
        out[it["id"]] = (sp,) + split_tests(r, it["card_tests"])
    return out, probs


def test_item(rules, it, tests, speaker, patient, rule_checks=True):
    """Self-tests for one item's phrases on one set of tests -> list of failures (empty = passed)."""
    f = []
    leak, extra = str_list(rules.get("leak")), str_list(rules.get("leak_extra"))
    unlock, asked = str_list(rules.get("unlock")), str_list(rules.get("asked"))
    from_card = it.get("leak_from_card") or []
    if rule_checks:
        for field, ph in (("leak", leak), ("leak_extra", extra), ("unlock", unlock), ("asked", asked)):
            for p in ph:
                try:
                    phrase_regex(p)
                except ValueError as e:
                    f.append(f"{field}: {e}")
                    continue
                if field in ("leak", "leak_extra") and too_common(p):
                    f.append(f"{field}: {p!r} is a single short word (needs 6+ letters or two words)")
        if f:
            return f
        if not leak:
            f.append("leak is empty")
        if not unlock:
            f.append("unlock is empty")
        if it["private_because"] and not asked:
            f.append("asked is empty (the item is private)")
        for label, text in it["allowed"]:
            m = matches(leak + extra + from_card, text)
            if m:
                f.append(f"leak/leak_extra {m} match text that may be said at any time ({label}): {text[:100]!r}")
    leak = leak + from_card
    for s in tests["disclosures"]:
        if not speaker_matches(leak, s, speaker, patient):
            f.append(f"leak matches no phrase in disclosure: {s!r}")
    for s in tests["safe_replies"]:
        m = speaker_matches(leak, s, speaker, patient)
        if m:
            f.append(f"leak {m} matches safe reply: {s!r}")
    for s in tests["unlock_questions"]:
        if not matches(unlock, s, True):
            f.append(f"unlock matches no phrase in unlock question: {s!r}")
    for s in tests["near_miss_questions"]:
        for field, ph in (("unlock", unlock), ("asked", asked)):
            m = matches(ph, s, True)
            if m:
                f.append(f"{field} {m} matches near-miss question: {s!r}")
    if asked and tests["unlock_questions"] and not any(matches(asked, s, True) for s in tests["unlock_questions"]):
        f.append("asked matches none of the unlock questions")
    return f


def check_phrases(draft, pl, tests):
    """-> (phrases by id, dev failures by id, held-out failures by id)."""
    got, dev, held = by_id(draft), {}, {}
    for it in pl["items"]:
        r = got.get(it["id"])
        if r is None:
            dev[it["id"]], held[it["id"]] = ["item missing from the answer"], []
            continue
        sp, td, th = tests[it["id"]]
        dev[it["id"]] = test_item(r, it, td, sp, pl["patient"])
        held[it["id"]] = test_item(r, it, th, sp, pl["patient"], rule_checks=False)
    return got, dev, held


def n_fails(fails):
    return sum(len(v) for v in fails.values())


def ask_tests(pl, tries, temperature, log):
    from gemma_client import chat
    msgs = [{"role": "user", "content": tests_prompt(pl)}]
    for attempt in range(1, tries + 1):
        raw = chat(msgs, temperature=temperature, max_tokens=8000)
        log.append({"call": "tests", "attempt": attempt, "answer": raw})
        try:
            tests, probs = check_tests(parse_json(raw), pl)
        except ValueError as e:
            tests, probs = {}, [str(e)]
        print(f"   tests, attempt {attempt}: {len(probs)} problem(s)")
        if not probs:
            return tests
        msgs += [{"role": "assistant", "content": raw},
                 {"role": "user", "content": "Problems:\n" + "\n".join(probs) + "\nAnswer with the full corrected JSON only."}]
    raise SystemExit(f"{pl['short']}: no usable tests in {tries} tries: {probs}")


def ask_phrases(pl, tests, tries, temperature, log):
    from gemma_client import chat
    speakers = {i: v[0] for i, v in tests.items()}
    msgs = [{"role": "user", "content": phrases_prompt(pl, speakers)}]
    best = None
    for attempt in range(1, tries + 1):
        raw = chat(msgs, temperature=temperature, max_tokens=8000)
        log.append({"call": "phrases", "attempt": attempt, "answer": raw})
        try:
            got, dev, held = check_phrases(parse_json(raw), pl, tests)
        except ValueError as e:
            got, dev, held = {}, {"(answer)": [str(e)]}, {}
        print(f"   phrases, attempt {attempt}: {n_fails(dev)} dev failure(s), {n_fails(held)} held-out failure(s)")
        if got and (best is None or n_fails(dev) < n_fails(best[1])):
            best = (got, dev, held, attempt)
        if n_fails(dev) == 0:
            break
        text = "\n".join(f"{i}: {x}" for i, xs in dev.items() for x in xs)
        msgs += [{"role": "assistant", "content": raw}, {"role": "user", "content": FIX.replace("@FAILS@", text)}]
    if best is None:
        raise SystemExit(f"{pl['short']}: no usable phrases in {tries} tries (see the log file)")
    return best


# ---------------------------------------------------------------- write / summary

HEADER = """# Hidden-item rules for {sid}, drafted by scripts/build_hidden_rules.py (v2)
# Reviewed by: PENDING
# private_from / private_because / not_checked_by_words and the card's own test lines were read from the
# role card by fixed code; speaker, tests and phrases were drafted by {source}.
# tests_dev failures were shown to the teacher; tests_held were never shown (an honest check).
# Phrase syntax: word* = any ending; [a|b] = either; "x ... y" = same sentence, at most 40 characters apart.
# After editing by hand, run: python3 scripts/build_hidden_rules.py {short} --test-only
{s3_note}"""
S3_NOTE = ("# s3 keeps its hand-written rules (make_conversations.py, run_probes.py, measure_teacher.py);\n"
           "# this file is only for comparing the drafted rules with them (compare_hidden_rules.py).\n")


def dump(path, head, data):
    path.write_text(head + "\n" + yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")


def write_rules(pl, got, tests, dev, held, source, attempts, out_dir):
    items = []
    for it in pl["items"]:
        r = got.get(it["id"], {})
        sp, td, th = tests.get(it["id"], (None, {k: [] for k in KINDS}, {k: [] for k in KINDS}))
        row = {"id": it["id"], "speaker": sp, "disclose_when": it["disclose_when"],
               "private_from": it["private_from"], "private_because": it["private_because"],
               "not_checked_by_words": it["not_checked_by_words"]}
        row["leak"] = str_list(r.get("leak"))
        row["leak_from_card"] = it["leak_from_card"]
        for k in ("leak_extra", "unlock", "asked"):
            row[k] = str_list(r.get(k))
        row["tests_dev"], row["tests_held"] = td, th
        row["self_test_dev"] = dev.get(it["id"]) or "passed"
        row["self_test_held"] = held.get(it["id"]) or "passed"
        items.append(row)
    data = {"scenario": pl["sid"], "short": pl["short"], "patient": pl["patient"],
            "in_room": [p["first"] for p in pl["people"] if p["in_room"]],
            "made": f"{datetime.datetime.now():%Y-%m-%d %H:%M}", "source": source, "attempts": attempts,
            "dev_failures": n_fails(dev), "held_failures": n_fails(held), "items": items}
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / f"{pl['short']}.yaml"
    dump(f, HEADER.format(sid=pl["sid"], short=pl["short"], source=source,
                          s3_note=S3_NOTE if pl["short"] == "s3" else ""), data)
    return f


def write_summary(out_dir):
    rows = []
    for f in sorted(out_dir.glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8"))
        if "held_failures" not in d:
            continue
        priv = [f"{i['id'].split('_')[0]} (from {', '.join(i['private_from']) or '??'})"
                for i in d["items"] if i.get("private_because")]
        rows.append(f"| {d['short']} | {len(d['items'])} | {'; '.join(priv) or '-'} | {d['dev_failures']} | "
                    f"{d['held_failures']} | {d['attempts']} | {d['made']} |")
    text = ("# Hidden-item rules: summary\n\nWritten by scripts/build_hidden_rules.py (v2). Reviewed by: PENDING\n\n"
            "Dev failures were shown to the teacher; held-out failures were not (the honest check).\n\n"
            "| Scenario | Items | Private items (who must be out of the room) | Dev failures | Held-out failures | "
            "Phrase attempts | Made |\n|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
    (out_dir / "summary.md").write_text(text, encoding="utf-8")


def retest(pl, out_dir):
    f = out_dir / f"{pl['short']}.yaml"
    if not f.exists():
        raise SystemExit(f"{f} does not exist")
    d = yaml.safe_load(f.read_text(encoding="utf-8"))
    by = {it["id"]: it for it in pl["items"]}
    dev_n = held_n = 0
    for row in d["items"]:
        it = dict(by[row["id"]])
        it["private_because"] = row.get("private_because")     # hand edits in the file win
        row.setdefault("leak_from_card", it["leak_from_card"])
        it["leak_from_card"] = row["leak_from_card"]
        dv = test_item(row, it, row["tests_dev"], row["speaker"], pl["patient"])
        hd = test_item(row, it, row["tests_held"], row["speaker"], pl["patient"], rule_checks=False)
        row["self_test_dev"], row["self_test_held"] = dv or "passed", hd or "passed"
        dev_n, held_n = dev_n + len(dv), held_n + len(hd)
        for x in dv:
            print(f"   {row['id']} (dev): {x}")
        for x in hd:
            print(f"   {row['id']} (held out): {x}")
    d["dev_failures"], d["held_failures"] = dev_n, held_n
    head = f.read_text(encoding="utf-8").split("\nscenario:", 1)[0]
    dump(f, head, d)
    print(f"   {pl['short']}: {dev_n} dev and {held_n} held-out failure(s)")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("scenario", help='short name (e.g. A2, C4-1, s3) or "all"')
    ap.add_argument("--plan", action="store_true", help="print what was read from the card(s); no model")
    ap.add_argument("--prompt", action="store_true", help="print the first prompt; no model")
    ap.add_argument("--draft", help='JSON written elsewhere: {"items": [{id, speaker, leak, leak_extra, unlock, '
                                    'asked, disclosures, safe_replies, unlock_questions, near_miss_questions}]}')
    ap.add_argument("--test-only", action="store_true", help="re-run the self-tests on the saved file")
    ap.add_argument("--tries", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--out", default=str(OUT), help="output folder (default evaluation/hidden_rules)")
    a = ap.parse_args()
    out_dir = pathlib.Path(a.out)

    sids = [d.name for d in scenario_dirs()]
    if a.scenario != "all":
        sids = [s for s in sids if short_of(s) == a.scenario]
        if not sids:
            raise SystemExit(f"no scenario with short name {a.scenario!r}; known: "
                             + ", ".join(short_of(d.name) for d in scenario_dirs()))
    if a.draft and len(sids) != 1:
        raise SystemExit("--draft works with one scenario")

    for sid in sids:
        pl = plan(sid)
        if a.plan:
            print_plan(pl)
            continue
        if a.prompt:
            print(tests_prompt(pl))
            continue
        if a.test_only:
            retest(pl, out_dir)
            continue
        print(f"== {pl['short']}")
        if a.draft:
            draft = parse_json(pathlib.Path(a.draft).read_text(encoding="utf-8"))
            tests, probs = check_tests(draft, pl)
            for p in probs:
                print(f"   tests: {p}")
            got, dev, held = check_phrases(draft, pl, tests)
            source, attempts = f"draft file {pathlib.Path(a.draft).name}", 1
        else:
            from gemma_client import model
            log = []
            try:
                tests = ask_tests(pl, a.tries, a.temperature, log)
                got, dev, held, attempts = ask_phrases(pl, tests, a.tries, a.temperature, log)
            finally:
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / f"{pl['short']}_teacher_log.json").write_text(
                    json.dumps(log, indent=1, ensure_ascii=False), encoding="utf-8")
            source = f"the teacher ({model()}, temperature {a.temperature})"
        f = write_rules(pl, got, tests, dev, held, source, attempts, out_dir)
        for kind, fails in (("dev", dev), ("held out", held)):
            for i, xs in fails.items():
                for x in xs:
                    print(f"   {i} ({kind}): {x}")
        print(f"   wrote {f.relative_to(ROOT) if f.is_relative_to(ROOT) else f} "
              f"({n_fails(dev)} dev, {n_fails(held)} held-out failure(s))")
    if not (a.plan or a.prompt):
        write_summary(out_dir)


if __name__ == "__main__":
    main()
