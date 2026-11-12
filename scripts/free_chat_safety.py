#!/usr/bin/env python3
"""
free_chat_safety.py
Minimum safety layer for the local free-text chat test (free_chat_server.py). Local testing only.

    looks_like_distress(text)      True if the person typing seems to be in real distress
    check_reply(text, facts)       list of reasons to withhold a patient reply ([] = show it)
    system_prompt(sid)             role card prompt + guideline layer
    load_facts(sid)                canonical facts read from the role card

The regular expressions and the CAG and medication checks are the ones in check_publish_v1.py.
These are simple pattern checks. They cannot tell whether a hidden item came out too early, or
catch every invented fact, so a reply that passes is not proven correct.
"""
import pathlib, re, sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import check_publish_v1 as cp

ROOT = cp.ROOT
GUIDELINES = ["prompts/layer3_guidelines/common/medication_safety.yaml.md",
              "prompts/layer3_guidelines/huntington/diagnosis.yaml.md",
              "prompts/layer3_guidelines/huntington/treatment.yaml.md"]
GUIDELINE_NOTE = """## Reference guidelines (the character does NOT know any of this)
The reference text below is for the people who built this simulation. The characters have never read
it. Never quote, paraphrase or use it, and never say any dose, number, range, score or rule from it.
If asked about any of it, say you do not know and that it is a question for the doctor."""
FINAL_NOTE = "Always reply in English, as the character, even if the clinician writes in another language."

# ---------------------------------------------------------------- the person typing
# First-person wording only, so that a trainee asking the patient "do you want to die?" does not stop
# the role-play. A false alarm is acceptable here; a miss is not, so quoted speech still triggers it.
NOT_ME = r"(?!you\b|she\b|he\b|they\b|ruth\b|anna\b|if\b|whether\b|people\b)"
GAP = rf"(?:{NOT_ME}[\w']+\s+){{0,3}}"
DISTRESS = [
    r"\b(?:kill|hurt|harm|cut|shoot|hang|poison)(?:ing)?\s+myself\b",
    r"\b(?:end|ending|take|taking)\s+my\s+(?:own\s+)?life\b",
    rf"\bi(?:'m|'d|\s+am|\s+would)?\s+{GAP}(?:want|wanna|wish|ready|going|deserve|hope|plan\w*)\s+(?:to\s+)?(?:die|be\s+dead)\b",
    r"\bi\s+wish\s+i\s+(?:was|were)\s+(?:dead|never\s+born)\b",
    rf"\bi\s+{GAP}(?:don't|do\s+not|can't|cannot)\s+(?:want\s+to\s+|wanna\s+)?(?:live|be\s+alive|be\s+here\s+anymore|wake\s+up|exist|go\s+on|keep\s+going|take\s+(?:it|this)\s+any\s*more|do\s+this\s+any\s*more)\b",
    r"\bi(?:'m|\s+am|\s+feel|\s+feel\s+so)\s+(?:\w+\s+)?suicidal\b",
    r"\bmy\s+suicidal\b|\bi\s+(?:keep\s+)?(?:think|thinking|have\s+thoughts?)\s+(?:about|of)\s+(?:suicide|ending\s+(?:it|things))\b",
    r"\bi\s+\w*\s*(?:want|wanna|going)\s+to\s+end\s+(?:it|it\s+all|things)\b",
    r"\b(?:no\s+reason\s+to\s+live|nothing\s+(?:left\s+)?to\s+live\s+for)\b",
    r"\b(?:better\s+off\s+without\s+me|better\s+off\s+dead)\b",
    r"我[^你她他]{0,6}(?:想|要|打算|准备)[^你她他]{0,4}(?:死|自杀|自残|结束.{0,4}生命)",
    r"我[^你她他]{0,6}(?:不想活|活不下去)",
    r"(?:伤害|杀了?|杀死)我?自己",
]


def looks_like_distress(text):
    t = text.replace("’", "'")
    return any(re.search(p, t, re.I) for p in DISTRESS)


# ---------------------------------------------------------------- the patient reply
NUM_WORDS = {w: i + 10 for i, w in enumerate("ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split())}
TENS = {w: (i + 2) * 10 for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split())}
UNITS = {w: i + 1 for i, w in enumerate("one two three four five six seven eight nine".split())}
NUM = (rf"\d{{1,3}}|(?:{'|'.join(TENS)})(?:[- ](?:{'|'.join(UNITS)}))?|{'|'.join(NUM_WORDS)}")
NOT_AN_AGE = r"(?![- ]?(?:minutes?|hours?|days?|weeks?|months?|miles?|km|blocks?|times?|percent|%))"
HEDGE = r"(?:\s+(?:only|just|nearly|almost|about))?"

DOSE = (r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|µg|ml|g|milligrams?|micrograms?)\b|"
        r"\b(?:\d+|two|three|four|five|six|seven|eight|nine|ten)\s+(?:tablets?|pills?|capsules?)\b|"
        r"\b(?:tablets?|pills?|capsules?|dose)\b[^.?!]{0,30}\b(?:three|four)\s+times\b")
EXTRA_MEDS = (r"haloperidol|amantadine|riluzole|memantine|donepezil|levodopa|warfarin|aspirin|insulin|metformin|"
              r"ibuprofen|acetaminophen|tylenol|botox|ssri")
NOT_MEDS = {"april", "magazine"}        # words that happen to match the drug-name endings in MED_TERMS
BREAK = (r"\bas an ai\b|\bi(?:'m| am) an ai\b|artificial intelligence|language model|\bchatbot\b|role[- ]?card|"
         r"system prompt|\bsimulat(?:ion|ed)\b|training (?:tool|scenario|exercise)|hidden item|disclose_when|"
         r"\bthe (?:character|trainee)\b|"
         r"\bh[1-4](?:_\w+)?\b|\b(?:did not|didn't|has not|hasn't|have not|haven't)(?: yet)? disclose\w*|"
         r"out of character|role[- ]?play\w*|\bprogrammed\b|\bmy instructions\b")
LIST = r"^\s*(?:[*\-•]|\d+[.)])\s+\*\*"      # a bold bullet list: a summary, not something a patient says
MEDICAL = (r"penetrance|autosomal|cyp2d6|metaboli[sz]er|\buhdrs\b|pba-s|phq-?9|c-ssrs|"
           r"\b\d{1,3}\s*%|\b\d{2}\s*(?:to|-|–)\s*\d{2}\s*(?:cag|repeats)\b|\bfifty percent\b|常染色体")
RELATIVE = r"husband|wife|daughter|son|sister|brother|mother|father|friend|grandson|granddaughter"
LABEL = r"^[*_ ]*([A-Z][a-z]+)[*_ ]*:[*_ ]*"


def num(s):
    s = s.lower()
    if s.isdigit():
        return int(s)
    if s in NUM_WORDS:
        return NUM_WORDS[s]
    parts = re.split(r"[- ]", s)
    return TENS[parts[0]] + (UNITS[parts[1]] if len(parts) > 1 else 0)


def load_facts(sid):
    card = yaml.safe_load((ROOT / "scenarios" / sid / "role_card.yaml").read_text(encoding="utf-8"))
    canon = card["family_canonical"]
    told = {k: card.get(k) for k in ("persona", "companion", "facts", "hidden", "ages_now", "family_canonical")}
    first = lambda who: str(who).split()[0]
    return {"sid": sid, "card": card, "patient": first(card["persona"]["name"]),
            "speakers": {first(card["persona"]["name"]), first(card["companion"]["name"])},
            "ages": dict(card["ages_now"]), "names": set(re.findall(r"\b[A-Z][a-z]+\b", yaml.safe_dump(told, allow_unicode=True))),
            "surname": canon["surname"], "relations": {k: first(canon[k]) for k in ("husband", "daughter", "son")},
            "cag": cp.cag_pairs("CAG " + str(canon["patient_HTT_CAG"])),
            # Only what the patient knows counts: mentor_only must not make a medicine acceptable.
            "med_text": yaml.safe_dump({k: card.get(k) for k in ("facts", "hidden")}, allow_unicode=True).lower()}


def split_speakers(text, facts):
    """Return [(speaker, text)]; a line with no label belongs to the patient. A second speaker on the same line is split off."""
    who = "|".join(sorted(facts["speakers"]))
    out = []
    for line in text.splitlines():
        if not line.strip():
            continue
        m = re.match(LABEL, line)
        speaker = m.group(1) if m else (out[-1][0] if out else facts["patient"])
        body = line[m.end():] if m else line
        parts = re.split(rf"(?<=[.!?\"])\s+[*_]*({who})[*_]*:[*_ ]*", body)
        out.append((speaker, parts[0].strip()))
        out += [(parts[i], parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)]
    return [(s, t) for s, t in out if t]


def check_ages(speaker, t, facts):
    ages, bad = facts["ages"], []
    for m in re.finditer(rf"\bI(?:'m|\s+am){HEDGE}\s+({NUM})\b{NOT_AN_AGE}", t, re.I):
        if num(m.group(1)) != ages.get(speaker):
            bad.append(m.group(0))
    for m in re.finditer(rf"\b({'|'.join(ages)})(?:'s|\s+is|\s+turned){HEDGE}\s+({NUM})\b{NOT_AN_AGE}", t, re.I):
        if num(m.group(2)) != ages[m.group(1).capitalize()]:
            bad.append(m.group(0))
    if speaker == facts["patient"]:
        for m in re.finditer(rf"\bmy\s+(husband|daughter|son)(?:'s|\s+is|\s+turned){HEDGE}\s+({NUM})\b{NOT_AN_AGE}", t, re.I):
            if num(m.group(2)) != ages[facts["relations"][m.group(1).lower()]]:
                bad.append(m.group(0))
    for m in re.finditer(rf"\b({NUM})[- ]years?[- ]old\b", t, re.I):
        if num(m.group(1)) not in ages.values():
            bad.append(m.group(0))
    return bad


def check_names(speaker, t, facts):
    bad = []
    for m in re.finditer(rf"\b[Mm]y\s+({RELATIVE})(?:,)?\s+([A-Z][a-z]+)\b", t):
        rel, name = m.group(1), m.group(2)
        wrong = speaker == facts["patient"] and rel in facts["relations"] and name != facts["relations"][rel]
        if wrong or name not in facts["names"]:
            bad.append(m.group(0))
    for m in re.finditer(r"\b(?:[Mm]y name is|I'm|I am|[Cc]all me)\s+([A-Z][a-z]+)\b(?!')", t):
        if m.group(1) not in {speaker, "Mrs", "Ms", "Miss", "Dr"}:
            bad.append(m.group(0))
    for m in re.finditer(rf"\b({'|'.join(sorted(facts['ages']))})\s+([A-Z][a-z]+)\b", t):
        if m.group(2) != facts["surname"]:
            bad.append(m.group(0))
    return bad


def check_cag(t, facts):
    pairs, bad = cp.cag_pairs(t), []
    bad += [f"{a}/{b}" for a, b in sorted(pairs - facts["cag"])]
    bad += [str(x) for x in sorted(cp.cag_singles(t) - {b for _, b in facts["cag"]})]
    return bad


def check_meds(t, facts):
    found = {m.group(0).lower() for m in re.finditer(rf"{cp.MED_TERMS}|\b(?:{EXTRA_MEDS})\b", t, re.I)} - NOT_MEDS
    return sorted(x for x in found if x.rstrip("s") not in facts["med_text"])


def check_selfharm(t):
    found = {4: []}
    cp.scan_forbidden(t, "reply", found)
    bad = [m for status, m in found[4] if status == cp.FAIL or not re.match(r"method term \((?:crash|drive)", m)]
    harm = re.search(cp.SELFHARM, t, re.I)      # no B2 fact touches this, so any mention is invented
    return bad + ([harm.group(0)] if harm else [])


def check_reply(text, facts):
    """Reasons to withhold this reply, as [(category, detail)]. Any failure in here also withholds it."""
    try:
        t = text.replace("’", "'").strip()
        reasons = []
        if not t:
            return [("empty", "")]
        if re.search(r"[぀-ヿ㐀-鿿가-힣]", t):
            reasons.append(("language", "not in English, so the checks cannot read it"))
        reasons += [("self-harm", x) for x in check_selfharm(t)]
        reasons += [("dose", m.group(0)) for m in re.finditer(DOSE, t, re.I)]
        reasons += [("character", m.group(0)) for m in re.finditer(BREAK, t, re.I)]
        reasons += [("character", "bold list") for _ in re.finditer(LIST, t, re.M)][:1]
        reasons += [("medical-fact", m.group(0)) for m in re.finditer(MEDICAL, t, re.I)]
        reasons += [("cag", x) for x in check_cag(t, facts)]
        reasons += [("medication", x) for x in check_meds(t, facts)]
        for speaker, part in split_speakers(t, facts):
            if speaker not in facts["speakers"]:
                reasons.append(("name", f"unknown speaker {speaker}"))
            reasons += [("age", x) for x in check_ages(speaker, part, facts)]
            reasons += [("name", x) for x in check_names(speaker, part, facts)]
        return reasons
    except Exception as e:      # fail closed: an unchecked reply is never shown
        return [("filter-error", type(e).__name__)]


def system_prompt(sid):
    base = (ROOT / "runtime" / "patient_prompts" / f"{sid}.md").read_text(encoding="utf-8").strip()
    guides = "\n\n".join((ROOT / p).read_text(encoding="utf-8").strip() for p in GUIDELINES)
    return "\n\n".join([base, GUIDELINE_NOTE, guides, FINAL_NOTE]) + "\n"
