#!/usr/bin/env python3
"""
build_hidden_rules.py  (distillation, all scenarios, step 1: leak / unlock rules from the role cards)

For s3 the words that decide "did a hidden item come out too early?" were written by hand
(UNLOCK, PRIVATE, ASKED in make_conversations.py; EARLY in measure_teacher.py; LEAK in run_probes.py).
This script drafts the same kind of rules for any scenario from its role card, so the other 14
scenarios can be generated, filtered and tested the same way.

Two parts:
  1. Read from the card with fixed code (no model):
       who is in the room (patient and companion; "others" such as a son on speakerphone are not),
       who must be out of the room before an item may come out ("while her mother is out of the room",
       "sees Anna alone"), and conditions that words cannot check ("AFTER the diagnosis has been
       given", "with Mark's agreement"), kept as notes for the semantic judge and for human review.
  2. Drafted by the teacher (31B), as short phrase lists rather than regular expressions:
       speaker      who reveals the item
       leak         words that can only mean the item came out (probes; early-disclosure check)
       leak_extra   wider "look at this" words (leak + leak_extra = the broad check, like EARLY)
       unlock       trainee words that meet disclose_when (topic only)
       asked        (private items only) a direct question about the item; a plain "yes" to it counts
       tests        example sentences the phrases must (or must not) match
     The script checks every draft (self-tests below) and sends the failures back to the teacher,
     up to --tries times. The draft with the fewest failures is kept.

Phrase syntax (case does not matter; whole words):
    suicid*            * at the end of a word = any ending (suicide, suicidal)
    end [my|her] life  [a|b] = either word
    kept ... tablets   ... = both parts in the same sentence, at most 40 characters apart

Self-tests (failures are written into the file):
    leak    matches every test disclosure; matches no safe reply; matches nothing the speaker may say
            at any time (trainee brief, opening line, facts, the item's partial_before / if_asked lines)
    unlock  matches every unlock question and no near-miss question
    asked   (private items) matches at least one unlock question and no near-miss question
The tests are written by the same model, so passing them is not proof. Read the file, and for s3
compare the drafted rules with the hand-written ones on the saved transcripts (next step).

Usage:
    python3 scripts/build_hidden_rules.py A2                  one scenario (calls the teacher)
    python3 scripts/build_hidden_rules.py all                 all 15 (s3 too, for the comparison)
    python3 scripts/build_hidden_rules.py all --plan          part 1 only: what was read from the cards
    python3 scripts/build_hidden_rules.py A2 --prompt         print the prompt that would be sent
    python3 scripts/build_hidden_rules.py A2 --draft d.json   use a draft written elsewhere (no teacher)
    python3 scripts/build_hidden_rules.py A2 --test-only      re-run the self-tests after editing the file

Writes evaluation/hidden_rules/<short>.yaml (Reviewed by: PENDING) and evaluation/hidden_rules/summary.md.
Short names: the part of the scenario folder name before the first "_" (s1, s2, s3, A1, ..., C4-1, ..., C5-3).
Other scripts read a file with load_rules(short). s3 keeps its hand-written rules for now.
"""
import argparse, datetime, json, pathlib, re, sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "evaluation" / "hidden_rules"
GAP = r"[^.?!\n]{0,40}?"
MIN_TESTS = 3


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


def phrase_regex(phrase):
    """One phrase in the syntax above -> a regular expression (string)."""
    p = " ".join(str(phrase).lower().split())
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


def regex_of(phrases):
    """A phrase list -> one pattern string, or None for an empty list."""
    ps = [phrase_regex(p) for p in phrases or []]
    return "|".join(f"(?:{x})" for x in ps) if ps else None


def matches(phrases, text):
    """The phrases in the list that match the text."""
    t = str(text).replace("’", "'")
    return [p for p in phrases or [] if re.search(phrase_regex(p), t, re.I)]


def load_rules(short):
    """Rules from evaluation/hidden_rules/<short>.yaml in the shapes the s3 code uses:
    unlock / asked / leak / early: {item_id: pattern}; private: [{"person": first name, "items": [ids]}].
    None if the file does not exist."""
    f = OUT / f"{short}.yaml"
    if not f.exists():
        return None
    d = yaml.safe_load(f.read_text(encoding="utf-8"))
    r = {"unlock": {}, "asked": {}, "leak": {}, "early": {}, "private": []}
    priv = {}
    for it in d["items"]:
        i = it["id"]
        for key, phrases in (("leak", it.get("leak")), ("early", (it.get("leak") or []) + (it.get("leak_extra") or [])),
                             ("unlock", it.get("unlock")), ("asked", it.get("asked"))):
            pat = regex_of(phrases)
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
                    "in_room": True, "will_leave_room": leave_text(c.get("will_leave_room"))})
    for o in as_list(card.get("others")):
        out.append({"name": o["name"], "role": "other", "relation": str(o.get("relation", "")), "in_room": False})
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


def flat(x):
    if isinstance(x, dict):
        return [s for v in x.values() for s in flat(v)]
    if isinstance(x, list):
        return [s for v in x for s in flat(v)]
    return [str(x)] if x not in (None, "") else []


def allowed_texts(card):
    """Text that may be said at any time: a leak phrase must match none of it. Includes the
    partial_before / if_asked lines of every hidden item (said before any item is earned)."""
    sc = card.get("scenario", {})
    out = [("trainee brief", " ".join(str(sc.get("trainee_brief", "")).split())),
           ("opening line", str(card["persona"].get("opening_line", "")))]
    out += [("facts", s) for s in flat(card.get("facts")) + flat(card.get("family_canonical"))]
    out += [(f"{h['id']} {k}", str(v)) for h in card.get("hidden", []) for k, v in h.items()
            if k == "partial_before" or k.startswith("if_")]
    return [(k, v) for k, v in out if v.strip()]


def plan(sid):
    raw = (ROOT / "scenarios" / sid / "role_card.yaml").read_text(encoding="utf-8")
    card = yaml.safe_load(raw)
    ppl = people(card)
    items = []
    for h in card.get("hidden", []):
        dw = " ".join(str(h.get("disclose_when", "")).split())
        who, why = private_rule(dw, ppl)
        items.append({"id": h["id"], "disclose_when": dw, "private_from": who, "private_because": why,
                      "not_checked_by_words": word_free_conditions(dw), "allowed": allowed_texts(card),
                      "card_item": h})
    return {"sid": sid, "short": short_of(sid), "card": card, "people": ppl, "items": items}


def print_plan(pl):
    print(f"\n== {pl['short']} ({pl['sid']})")
    print("   people: " + "; ".join(f"{p['first']} ({p['role']}" + (", not in room" if not p["in_room"] else "")
                                    + (f", leaves: {p['will_leave_room']}" if "will_leave_room" in p else "") + ")"
                                    for p in pl["people"]))
    for it in pl["items"]:
        line = f"   {it['id']}"
        if it["private_because"]:
            line += f"  PRIVATE from {it['private_from'] or '?? (name not found)'}  [{it['private_because']}]"
        if it["not_checked_by_words"]:
            line += f"  not checked: {it['not_checked_by_words']}"
        print(line)


# ---------------------------------------------------------------- part 2: the teacher's draft

EXAMPLE = {"items": [{
    "id": "H1_stopped_pills", "speaker": "Joan",
    "leak": ["stopped ... [pills|tablets|medicine*|medication*]", "not [taking|been taking] ... [pills|tablets]",
             "haven't [taken|been taking] ... [pills|tablets]", "[skip|skipped|skipping] ... [pills|tablets|doses]",
             "Tom doesn't know", "don't tell Tom"],
    "leak_extra": ["dizzy", "blood pressure [pills|tablets]", "three weeks"],
    "unlock": ["[medicine*|medication*|pills|tablets]", "blood pressure", "side effect*"],
    "asked": ["[stopped|skipping|missing] ... [pills|tablets|medicine*|doses]",
              "[taking|take] ... [pills|tablets|medicine*] ... [every day|regularly|as prescribed]"],
    "tests": {
        "disclosures": ["Joan: I stopped those pills a few weeks ago. They made me so dizzy.",
                        "Joan: (quietly) I haven't been taking the blood pressure ones.",
                        "Joan: I skip them most days, if I'm honest.",
                        "Joan: Please don't tell Tom. He'd only worry."],
        "safe_replies": ["Joan: I'm fine. A bit dizzy sometimes, that's all.",
                         "Joan: Why does everyone keep asking about my pills?",
                         "Joan: Tom drove me here. He's very good to me.",
                         "Joan: My knees are the real trouble."],
        "unlock_questions": ["How are the medicines going for you, Joan?",
                             "Some people find their tablets hard to take. How is it for you?",
                             "Have the blood pressure pills given you any side effects?",
                             "Tell me about your medication."],
        "near_miss_questions": ["Have you had any falls lately?", "How is Tom coping?",
                                "How are you sleeping?", "What do you do during the day?"]}}]}
EXAMPLE_CARD = ('(Example card: patient Joan Price, 70, with her son Tom. Hidden item H1_stopped_pills: "Joan stopped '
                'her blood-pressure pills three weeks ago because they made her dizzy. Tom does not know." '
                'disclose_when: "Trainee asks Joan, while Tom is out of the room, an open question about how her '
                'medicines are going." private: true)')

PROMPT = """You help build an automatic checker for a clinical-communication training simulator.
A language model plays a fictional patient and family members. Each person has hidden items: things
they reveal only when the trainee asks in the right way (disclose_when). We need simple word rules
that catch a hidden item coming out too early, and that show when the trainee has asked the question
that earns it.

For EVERY hidden item of the scenario below, write short phrase lists in this syntax (case does not
matter; phrases match whole words):
  suicid*            * at the end of a word = any ending
  end [my|her] life  [a|b] = either word (no empty choices)
  kept ... tablets   ... = both parts in the same sentence, at most 40 characters apart

Fields for each item:
  id           the item id
  speaker      the first name of the person who reveals it (one of: @NAMES@)
  leak         4 to 12 phrases the speaker would use ONLY when giving this item away. Cover first person
               and, if another family member might repeat it, third person. A leak phrase must NOT match
               anything in trainee_brief, opening_line, facts_not_secret or the item's allowed_lines: those
               may be said at any time. Prefer specific two-part phrases ("kept ... tablets") to single
               common words.
  leak_extra   0 to 8 wider phrases worth a human look (these may overlap with the brief).
  unlock       4 to 12 phrases a trainee would use when asking the question in disclose_when. Words can
               only check the TOPIC of the question, not its tone, its order, or who is in the room (the
               script tracks who is in the room). Do not unlock on a nearby topic that disclose_when does
               not name: for example, if disclose_when needs "plans or preparations", a question that only
               names tablets must not unlock.
  asked        only if the item has "private": true: 2 to 8 phrases for a DIRECT question about the item
               itself, so that a plain "yes" to it counts as a disclosure. Otherwise [].
  tests        disclosures: 4 replies by the speaker that give the item away, in different words (one indirect).
               safe_replies: 4 in-character replies that do NOT give it away (a deflection, the allowed
                 lines, and talk about nearby facts that are not secret).
               unlock_questions: 4 trainee lines that meet disclose_when.
               near_miss_questions: 4 trainee lines on a nearby topic that do NOT meet disclose_when
                 (never lines that differ only in tone or kindness).
               Start each reply with the speaker's first name and a colon. Add no facts beyond the card.
               Never write self-harm methods, amounts or doses.

The script will test that: leak matches every disclosure, no safe reply and no allowed text; unlock
matches every unlock question and no near-miss question; asked matches at least one unlock question
and no near-miss question.

Answer with JSON only, no other text. A made-up example (not one of our scenarios):
@EXAMPLE_CARD@
@EXAMPLE@

The scenario:
@CARD@
"""

FIX = """Your rules failed these self-tests:
@FAILS@
Change the phrases so that every test passes. Change a test sentence only if it breaks the instructions.
Answer with the full corrected JSON for ALL items, JSON only."""


def card_view(pl):
    card = pl["card"]
    sc = card.get("scenario", {})
    items = []
    for it in pl["items"]:
        h = it["card_item"]
        v = {"id": h["id"], "content": " ".join(str(h.get("content", "")).split()), "disclose_when": it["disclose_when"],
             "allowed_lines": {k: str(h[k]) for k in h if k == "partial_before" or k.startswith("if_")},
             "private": bool(it["private_because"])}
        items.append(v)
    view = {"setting": sc.get("setting"), "trainee_brief": " ".join(str(sc.get("trainee_brief", "")).split()),
            "opening_line": card["persona"].get("opening_line"),
            "people": [{"name": p["name"], "role": p["role"], "relation": p["relation"],
                        "in_the_room": p["in_room"]} for p in pl["people"]],
            "facts_not_secret": card.get("facts"), "hidden_items": items}
    return json.dumps(view, indent=1, ensure_ascii=False, default=str)


def prompt_for(pl):
    names = ", ".join(p["first"] for p in pl["people"])
    return (PROMPT.replace("@NAMES@", names).replace("@EXAMPLE_CARD@", EXAMPLE_CARD)
            .replace("@EXAMPLE@", json.dumps(EXAMPLE, indent=1)).replace("@CARD@", card_view(pl)))


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


def test_item(rules, it, names):
    """Self-tests for one item's rules -> list of failures (empty = passed)."""
    f = []
    if str(rules.get("speaker", "")).split(" ")[0] not in names:
        f.append(f"speaker {rules.get('speaker')!r} is not one of {names}")
    for field in ("leak", "leak_extra", "unlock", "asked"):
        for p in str_list(rules.get(field)):
            try:
                phrase_regex(p)
            except ValueError as e:
                f.append(f"{field}: {e}")
    if f:
        return f
    t = rules.get("tests") or {}
    need = ["disclosures", "safe_replies", "unlock_questions", "near_miss_questions"]
    for k in need:
        if len(str_list(t.get(k))) < MIN_TESTS:
            f.append(f"tests.{k}: fewer than {MIN_TESTS} sentences")
    leak, unlock, asked = str_list(rules.get("leak")), str_list(rules.get("unlock")), str_list(rules.get("asked"))
    if not leak:
        f.append("leak is empty")
    if not unlock:
        f.append("unlock is empty")
    if it["private_because"] and not asked:
        f.append("asked is empty (the item is private)")
    for s in str_list(t.get("disclosures")):
        if not matches(leak, s):
            f.append(f"leak matches no phrase in disclosure: {s!r}")
    for s in str_list(t.get("safe_replies")):
        m = matches(leak, s)
        if m:
            f.append(f"leak {m} matches safe reply: {s!r}")
    for label, text in it["allowed"]:
        m = matches(leak, text)
        if m:
            f.append(f"leak {m} matches text that may be said at any time ({label}): {text[:100]!r}")
    for s in str_list(t.get("unlock_questions")):
        if not matches(unlock, s):
            f.append(f"unlock matches no phrase in unlock question: {s!r}")
    for s in str_list(t.get("near_miss_questions")):
        for field, ph in (("unlock", unlock), ("asked", asked)):
            m = matches(ph, s)
            if m:
                f.append(f"{field} {m} matches near-miss question: {s!r}")
    if asked and not any(matches(asked, s) for s in str_list(t.get("unlock_questions"))):
        f.append("asked matches none of the unlock questions")
    return f


def check_draft(draft, pl):
    names = [p["first"] for p in pl["people"]]
    got = {str(r.get("id")): r for r in draft.get("items", []) if isinstance(r, dict)} if isinstance(draft, dict) else {}
    fails = {}
    for it in pl["items"]:
        r = got.get(it["id"])
        fails[it["id"]] = ["item missing from the answer"] if r is None else test_item(r, it, names)
    return got, fails


def n_fails(fails):
    return sum(len(v) for v in fails.values())


def ask_teacher(pl, tries, temperature, log):
    from gemma_client import chat
    msgs = [{"role": "user", "content": prompt_for(pl)}]
    best = None
    for attempt in range(1, tries + 1):
        raw = chat(msgs, temperature=temperature, max_tokens=8000)
        log.append({"attempt": attempt, "answer": raw})
        try:
            got, fails = check_draft(parse_json(raw), pl)
        except ValueError as e:
            got, fails = {}, {"(answer)": [str(e)]}
        n = n_fails(fails)
        print(f"   attempt {attempt}: {n} self-test failure(s)")
        if got and (best is None or n < best[2]):
            best = (got, fails, n, attempt)
        if n == 0:
            break
        text = "\n".join(f"{i}: {x}" for i, xs in fails.items() for x in xs)
        msgs += [{"role": "assistant", "content": raw}, {"role": "user", "content": FIX.replace("@FAILS@", text)}]
    if best is None:
        raise SystemExit(f"{pl['short']}: no usable answer from the teacher in {tries} tries (see the log file)")
    return best


# ---------------------------------------------------------------- write / summary

HEADER = """# Hidden-item rules for {sid}, drafted by scripts/build_hidden_rules.py
# Reviewed by: PENDING
# private_from / private_because / not_checked_by_words were read from the role card by fixed code;
# speaker, leak, leak_extra, unlock, asked and tests were drafted by {source}.
# Phrase syntax: word* = any ending; [a|b] = either; "x ... y" = same sentence, at most 40 characters apart.
# After editing by hand, run: python3 scripts/build_hidden_rules.py {short} --test-only
{s3_note}"""
S3_NOTE = ("# s3 keeps its hand-written rules (make_conversations.py, run_probes.py, measure_teacher.py);\n"
           "# this file is only for comparing the drafted rules with them.\n")


def write_rules(pl, got, fails, source, attempts, out_dir):
    items = []
    for it in pl["items"]:
        r = got.get(it["id"], {})
        row = {"id": it["id"], "speaker": r.get("speaker"), "disclose_when": it["disclose_when"],
               "private_from": it["private_from"], "private_because": it["private_because"],
               "not_checked_by_words": it["not_checked_by_words"]}
        for k in ("leak", "leak_extra", "unlock", "asked"):
            row[k] = str_list(r.get(k))
        row["tests"] = {k: str_list((r.get("tests") or {}).get(k))
                        for k in ("disclosures", "safe_replies", "unlock_questions", "near_miss_questions")}
        row["self_test"] = fails.get(it["id"]) or "passed"
        items.append(row)
    data = {"scenario": pl["sid"], "short": pl["short"],
            "in_room": [p["first"] for p in pl["people"] if p["in_room"]],
            "made": f"{datetime.datetime.now():%Y-%m-%d %H:%M}", "source": source, "attempts": attempts,
            "self_test_failures": n_fails(fails), "items": items}
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / f"{pl['short']}.yaml"
    head = HEADER.format(sid=pl["sid"], short=pl["short"], source=source,
                         s3_note=S3_NOTE if pl["short"] == "s3" else "")
    f.write_text(head + "\n" + yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")
    return f


def write_summary(out_dir):
    rows = []
    for f in sorted(out_dir.glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8"))
        priv = [f"{i['id'].split('_')[0]} (from {', '.join(i['private_from']) or '??'})"
                for i in d["items"] if i.get("private_because")]
        bad = [f"{i['id'].split('_')[0]}: {len(i['self_test'])}" for i in d["items"] if i["self_test"] != "passed"]
        rows.append(f"| {d['short']} | {len(d['items'])} | {'; '.join(priv) or '-'} | "
                    f"{'; '.join(bad) or 'all passed'} | {d['source']} | {d['made']} |")
    text = ("# Hidden-item rules: summary\n\nWritten by scripts/build_hidden_rules.py. Reviewed by: PENDING\n\n"
            "| Scenario | Items | Private items (who must be out of the room) | Self-test failures | Drafted by | Made |\n"
            "|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
    (out_dir / "summary.md").write_text(text, encoding="utf-8")


def retest(pl, out_dir):
    f = out_dir / f"{pl['short']}.yaml"
    if not f.exists():
        raise SystemExit(f"{f} does not exist")
    d = yaml.safe_load(f.read_text(encoding="utf-8"))
    names = [p["first"] for p in pl["people"]]
    by_id = {it["id"]: it for it in pl["items"]}
    total = 0
    for row in d["items"]:
        it = dict(by_id[row["id"]])
        it["private_because"] = row.get("private_because")     # a hand edit in the file wins
        fails = test_item(row, it, names)
        row["self_test"] = fails or "passed"
        total += len(fails)
        for x in fails:
            print(f"   {row['id']}: {x}")
    d["self_test_failures"] = total
    head = f.read_text(encoding="utf-8").split("\n" + "scenario:", 1)[0]
    f.write_text(head + "\n" + yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")
    print(f"   {pl['short']}: {total} self-test failure(s)")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("scenario", help='short name (e.g. A2, C4-1, s3) or "all"')
    ap.add_argument("--plan", action="store_true", help="print what was read from the card(s); no model")
    ap.add_argument("--prompt", action="store_true", help="print the prompt; no model")
    ap.add_argument("--draft", help="JSON draft written elsewhere, instead of asking the teacher")
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
            print(prompt_for(pl))
            continue
        if a.test_only:
            retest(pl, out_dir)
            continue
        print(f"== {pl['short']}")
        if a.draft:
            got, fails = check_draft(parse_json(pathlib.Path(a.draft).read_text(encoding="utf-8")), pl)
            source, attempts = f"draft file {pathlib.Path(a.draft).name}", 1
        else:
            from gemma_client import model
            log = []
            try:
                got, fails, _, attempts = ask_teacher(pl, a.tries, a.temperature, log)
            finally:
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / f"{pl['short']}_teacher_log.json").write_text(
                    json.dumps(log, indent=1, ensure_ascii=False), encoding="utf-8")
            source = f"the teacher ({model()}, temperature {a.temperature})"
        f = write_rules(pl, got, fails, source, attempts, out_dir)
        for i, xs in fails.items():
            for x in xs:
                print(f"   {i}: {x}")
        print(f"   wrote {f.relative_to(ROOT) if f.is_relative_to(ROOT) else f} ({n_fails(fails)} self-test failure(s))")
    if not (a.plan or a.prompt):
        write_summary(out_dir)


if __name__ == "__main__":
    main()
