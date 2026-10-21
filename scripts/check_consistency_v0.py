#!/usr/bin/env python3
"""
check_consistency_v0.py

v0 consistency checker for a synthetic consult note + its Canonical Facts Sheet.
Built and tested on the Huntington demo only. It compares the note text with the fact
sheet and a few written rules. It does NOT judge whether content is clinically correct.

Usage:
    python3 scripts/check_consistency_v0.py demos/huntington_demo_v2.md

Checks:
    1  All 12 sections (and 10.1 to 10.5) present, titled and ordered as in the skeleton
    2  Dates: fact-sheet timeline sorted; note dates covered by the timeline; no future
       dates in the main note; addendum later than the consultation
    3  Values: scale scores, CAG repeat numbers and QTc match the fact sheet
    4  Left/right: not applicable when the fact sheet has no side (diffuse disease)
    5  Final diagnosis is not listed among the excluded differentials
    6  Tetrabenazine titration follows the guideline layer (huntington/treatment, hd-tx-001)
"""
import re
import sys
from datetime import date, timedelta

import yaml

SKELETON = [("1", "reason for referral"), ("2", "history of present illness"),
            ("3", "past medical history"), ("4", "past surgical history"),
            ("5", "medications"), ("6", "allergies"), ("7", "social history"),
            ("8", "family history"), ("9", "physical and neurological examination"),
            ("10", "investigations"), ("11", "assessment"), ("12", "plan"),
            ("10.1", "laboratory"), ("10.2", "neuroimaging"), ("10.3", "pathology"),
            ("10.4", "molecular/genomic"), ("10.5", "csf")]

PASS, FAIL, NA = "PASS", "FAIL", "N/A"


def norm(s):
    return re.sub(r"\s*/\s*", "/", s.strip().lower())


def split_doc(text, start_marker="# Movement Disorders Clinic"):
    """Return (body, main_note, addendum, facts_dict)."""
    i = text.find("# Canonical Facts Sheet")
    facts_part = text[i:] if i >= 0 else ""
    body = text[:i] if i >= 0 else text
    s = body.find(start_marker)
    if s >= 0:
        body = body[s:]
    k = body.find("\n# Addendum")
    main, addendum = (body[:k], body[k:]) if k >= 0 else (body, "")
    m = re.search(r"```yaml\n(.*?)```", facts_part, re.S)
    facts = yaml.safe_load(m.group(1)) if m else None
    return body, main, addendum, facts


def get(d, *path):
    for p in path:
        if not isinstance(d, dict) or p not in d:
            return None
        d = d[p]
    return d


# ---------------------------------------------------------------- check 1
def check_sections(body):
    problems = []
    heads = re.findall(r"^#{2,3}\s+(\d+(?:\.\d+)?)\.?\s+(.*)$", body, re.M)
    found = {num: norm(title) for num, title in heads}
    for num, title in SKELETON:
        if num not in found:
            problems.append(f"missing section {num} ({title})")
        elif found[num] != title:
            problems.append(f"section {num} is titled '{found[num]}', expected '{title}'")
    mains = [int(n) for n, _ in heads if re.fullmatch(r"\d+", n)]
    if mains != sorted(mains):
        problems.append("main sections are out of order")
    return problems


# ---------------------------------------------------------------- check 2
def parse_key(k):
    k = str(k)
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})_to_(?:(\d{4})-(\d{2})-)?(\d{2})", k)
    if m:
        y, mo, d1, y2, mo2, d2 = m.groups()
        return (date(int(y), int(mo), int(d1)),
                date(int(y2 or y), int(mo2 or mo), int(d2)))
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", k)
    if m:
        d = date(*map(int, m.groups()))
        return d, d
    m = re.fullmatch(r"(\d{4})-(\d{2})", k)
    if m:
        y, mo = map(int, m.groups())
        nxt = date(y + (mo == 12), (mo % 12) + 1, 1)
        return date(y, mo, 1), nxt - timedelta(days=1)
    return None


def dates_in(text):
    out = []
    for s in re.findall(r"\d{4}-\d{2}-\d{2}", text):
        try:
            out.append((s, date.fromisoformat(s)))
        except ValueError:
            pass
    return out


def check_dates(body, main, addendum, facts):
    problems = []
    # Date of birth is not an event, so leave it out of the timeline checks.
    drop_dob = lambda t: re.sub(r"\*\*DOB:\*\*\s*\d{4}-\d{2}-\d{2}", "**DOB:** (removed)", t)
    body, main, addendum = drop_dob(body), drop_dob(main), drop_dob(addendum)
    timeline = get(facts, "timeline") or {}
    spans = []
    for k in timeline:
        sp = parse_key(k)
        if sp is None:
            problems.append(f"timeline key '{k}' is not a recognised date format")
        else:
            spans.append(sp)
    starts = [s for s, _ in spans]
    if starts != sorted(starts):
        problems.append("fact-sheet timeline is not in chronological order")
    for s, d in dates_in(body):
        if not any(a <= d <= b for a, b in spans):
            problems.append(f"date {s} in the note is not covered by the fact-sheet timeline")
    cm = re.search(r"\*\*Date of consultation:\*\*\s*(\d{4}-\d{2}-\d{2})", body)
    am = re.search(r"^# Addendum[^\n]*\((\d{4}-\d{2}-\d{2})\)", addendum.lstrip("\n"), re.M)
    if cm:
        consult = date.fromisoformat(cm.group(1))
        for s, d in dates_in(main):
            if d > consult:
                problems.append(f"main note (dated {consult}) mentions later date {s}")
        if am and date.fromisoformat(am.group(1)) <= consult:
            problems.append(f"addendum date {am.group(1)} is not after the consultation {consult}")
    if am:
        ad = date.fromisoformat(am.group(1))
        for s, d in dates_in(addendum):
            if d > ad:
                problems.append(f"addendum (dated {ad}) mentions later date {s}")
    return sorted(set(problems))


# ---------------------------------------------------------------- check 3
def lead_number(v):
    m = re.match(r"\s*(\d+(?:\.\d+)?)", str(v))
    return m.group(1) if m else None


SCORE_RULES = [
    ("UHDRS total motor score", r"Total Motor Score(?: \(TMS\))?:?\s*(\d+)/124", "UHDRS_TMS"),
    ("UHDRS total functional capacity", r"(?:Total Functional Capacity \(TFC\)|TFC):?\s*(\d+)/13", "UHDRS_TFC"),
    ("UHDRS functional assessment", r"Functional Assessment Scale:\s*(\d+)/25", "UHDRS_functional_assessment"),
    ("PBA-s irritability", r"Irritability:\s*(\d+)", "PBA_s_irritability"),
    ("PBA-s apathy", r"Apathy:\s*(\d+)", "PBA_s_apathy"),
    ("MoCA", r"MoCA:?\s*(\d+)/30", "MoCA"),
    ("SDMT", r"\(SDMT\):\s*(\d+)", "SDMT"),
    ("Letter fluency", r"Letter fluency:\s*(\d+) words", "letter_fluency_3min"),
    ("PHQ-9", r"PHQ-9(?: =|:)\s*(\d+)", "PHQ9"),
]


def check_values(body, facts):
    problems, notes = [], []
    scores = get(facts, "clinical", "severity_scores") or {}
    for label, pattern, key in SCORE_RULES:
        exp = lead_number(scores.get(key))
        if exp is None:
            problems.append(f"{label}: no value '{key}' in fact sheet")
            continue
        got = re.findall(pattern, body)
        if not got:
            problems.append(f"{label}: expected {exp} but it does not appear in the note")
        elif any(g != exp for g in got):
            problems.append(f"{label}: fact sheet {exp}, note has {sorted(set(got))}")
        else:
            notes.append(f"{label} {exp} x{len(got)}")
    # QTc
    q = re.search(r"QTc (\d+)", str(get(facts, "safety_and_screening", "baseline_screening")))
    if q:
        got = re.findall(r"QTc (\d+)\s*ms", body)
        if any(g != q.group(1) for g in got):
            problems.append(f"QTc: fact sheet {q.group(1)}, note has {sorted(set(got))}")
        elif not got:
            problems.append(f"QTc: expected {q.group(1)} but it does not appear in the note")
    # CAG repeats
    a = re.search(r"alleles (\d+) and (\d+)", str(get(facts, "investigations", "molecular", "key_results")))
    if a:
        allowed = {a.group(1), a.group(2)}
        nums = set()
        for g1, g2 in re.findall(r"(\d+)(?:\s+and\s+(\d+))?\s+(?:CAG\s+)?repeats", body):
            nums.add(g1)
            if g2:
                nums.add(g2)
        bad = sorted(n for n in nums if n not in allowed)
        if bad:
            problems.append(f"CAG repeats: fact sheet {sorted(allowed)}, note has {bad}")
        elif not nums:
            problems.append("CAG repeats: no repeat numbers found in the note")
    return problems


# ---------------------------------------------------------------- check 4
def check_laterality(facts):
    dist = str(get(facts, "investigations", "imaging", "lesion_distribution") or "").lower()
    if not re.search(r"\b(left|right)\b", dist):
        return None
    return ["fact sheet has a side, but v0 does not implement laterality checks yet"]


# ---------------------------------------------------------------- check 5
def check_diagnosis_not_excluded(body, facts):
    problems = []
    diag = str(get(facts, "clinical", "diagnosis") or "")
    term = diag.split(",")[0].strip().lower()
    if not term:
        return ["no diagnosis in fact sheet"]
    for item in get(facts, "differential") or []:
        if term in str(item.get("diagnosis", "")).lower():
            problems.append(f"fact-sheet differential lists the final diagnosis: {item.get('diagnosis')}")
    m = re.search(r"\*\*Differential diagnosis[^\n]*\n((?:- .*\n?)+)", body)
    if m:
        for line in m.group(1).splitlines():
            name = line[2:].split(":")[0].lower()
            if term in name:
                problems.append(f"note lists the final diagnosis as an excluded alternative: '{name.strip()}'")
    return problems


# ---------------------------------------------------------------- check 6
def check_tetrabenazine(body):
    if "tetrabenazine" not in body.lower():
        return None
    problems = []
    for phrase in ("12.5 mg once daily", "12.5 mg twice daily"):
        if phrase not in body:
            problems.append(f"required titration step not found: '{phrase}'")
    if "37.5" in body and "three divided doses" not in body:
        problems.append("37.5 to 50 mg/day is mentioned without 'three divided doses'")
    for v in re.findall(r"max(?:imum)?\.?\s+single\s+dose(?:\s+of)?\s*(\d+(?:\.\d+)?)\s*mg", body, re.I):
        if float(v) > 25:
            problems.append(f"single-dose cap {v} mg is above 25 mg")
    for para in body.split("\n"):
        for sent in re.split(r"(?<=[.])\s+(?=[A-Z])", para):
            doses = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*mg/day", sent)]
            if any(d > 50 for d in doses) and "CYP2D6" not in sent:
                problems.append(f"daily dose above 50 mg without CYP2D6 in the same sentence: '{sent.strip()[:90]}'")
    return problems


# ---------------------------------------------------------------- runner
def run_checks(text):
    body, main, addendum, facts = split_doc(text)
    if facts is None:
        return [("0", "Fact sheet found", FAIL, ["no ```yaml block after '# Canonical Facts Sheet'"])]
    out = []
    p = check_sections(body)
    out.append(("1", "12 sections present and ordered", FAIL if p else PASS, p))
    p = check_dates(body, main, addendum, facts)
    out.append(("2", "Dates in order and covered by timeline", FAIL if p else PASS, p))
    p = check_values(body, facts)
    out.append(("3", "Scores, CAG repeats, QTc match fact sheet", FAIL if p else PASS, p))
    p = check_laterality(facts)
    out.append(("4", "Left/right consistent", NA if p is None else FAIL, p or ["no side in fact sheet (diffuse disease)"]))
    p = check_diagnosis_not_excluded(body, facts)
    out.append(("5", "Final diagnosis not listed as excluded", FAIL if p else PASS, p))
    p = check_tetrabenazine(body)
    if p is None:
        out.append(("6", "Tetrabenazine titration follows guidance", NA, ["drug not mentioned"]))
    else:
        out.append(("6", "Tetrabenazine titration follows guidance", FAIL if p else PASS, p))
    return out


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    text = open(sys.argv[1], encoding="utf-8").read()
    results = run_checks(text)
    for num, name, status, msgs in results:
        print(f"[{status}] Check {num}: {name}")
        if status != PASS:
            for m in msgs:
                print(f"        - {m}")
    n_fail = sum(1 for r in results if r[2] == FAIL)
    print(f"\n{n_fail} check(s) failed.")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
