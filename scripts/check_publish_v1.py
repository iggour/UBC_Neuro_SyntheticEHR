#!/usr/bin/env python3
"""
check_publish_v1.py

Automated pre-publication check for every scenario folder. Extends the v0 idea (compare text with
canonical facts and written rules) from consult notes to scenarios; the structure and family checks
in check_role_cards.py are reused here. It does NOT judge whether content is clinically correct.

Usage:
    python3 scripts/check_publish_v1.py                  (all checks, writes docs/publish_check_report.md)
    python3 scripts/check_publish_v1.py --no-links       (skip the live link check)
    python3 scripts/check_publish_v1.py --root DIR --report FILE     (check a copy of the repo)

Checks (each reports PASS / WARN / FAIL per scenario):
    1  Numbers: CAG values and category claims, ages, onset type vs age and CAG
    2  Family consistency: names, ages, timeline, CAG, medications
    3  Required items: source URLs with check dates, disclaimer, 9-8-8 for suicide/safety scenarios,
       and a content warning shown on the site where suicide or violence is the core of the scenario
    4  Forbidden content: self-harm method details, quantities or doses linked to self-harm
    5  Source links: live request to every URL (404/410/DNS failure = broken)
    6  Readability of the family prep sheet (Flesch-Kincaid grade)

Risk tier: high = suicide, safety, medication, minors testing or legal; otherwise low.
High-risk scenarios can never auto-pass: their decision is always "needs human review".
Exit code: 0 only if every scenario auto-passes, otherwise 1.
"""
import argparse, concurrent.futures, datetime, pathlib, re, subprocess, sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import check_role_cards as crc

ROOT = pathlib.Path(__file__).resolve().parent.parent
PASS, WARN, FAIL, NA = "PASS", "WARN", "FAIL", "N/A"
RANK = {NA: 0, PASS: 1, WARN: 2, FAIL: 3}
CHECKS = {1: "Numbers", 2: "Family", 3: "Required", 4: "Forbidden", 5: "Links", 6: "Readability"}
NOTICE = "All patients are fictional. AI-generated content for education only. Not medical advice."

# CAG categories; same ranges as the reviewed knowledge cards ([s1] in s1_pretest_counselling).
CAG_CATS = {"normal": (0, 26), "intermediate": (27, 35), "reduced penetrance": (36, 39), "full penetrance": (40, 999)}
CAG_MIN, CAG_MAX = 9, 130
ONSET = {"juvenile": (0, 20), "adult": (21, 59), "late": (60, 110)}
# Plausibility only: outside these, onset type and CAG look mismatched, so a human should look.
ONSET_CAG = {"juvenile": (50, 999), "adult": (36, 59), "late": (36, 44)}
AGE_MAX = 110
READ_PASS, READ_WARN = 8.0, 10.0      # Flesch-Kincaid grade: <=8 PASS, <=10 WARN, above FAIL
# Scenarios built around suicide or violence. Others only mention screening or general safety, and
# a warning on every one would soon go unread. Add a scenario here when that is its main subject.
CONTENT_WARNING = {"s3_suicide_risk_assessment", "C4-3_partner_safety_and_minor_testing"}
STALE_DAYS = 180                      # law and trial sources must be re-checked within this time

RISK = {
    "suicide": r"suicid|self-harm",
    "safety": r"\bsafety\b|\bsafe\b|\bunsafe\b|violence|firearm|seizure|driving",
    "medication": r"medication|tetrabenazine|\bdoses?\b|antidepressant",
    "minors testing": r"(test\w*).{0,60}\b(child|children|minor|minors|under 18|teen\w*|daughter|son)\b"
                      r"|\b(child|children|minor|minors|under 18|teen\w*)\b.{0,60}\btest",
    "legal": r"\blegal\b|\blaw\b|\blaws\b|insurance|non-discrimination|human rights|substitute decision"
             r"|\bcapacity\b|unfit to drive|confidentiality|advance care|representation agreement|decision[- ]maker|feeding tube",
}
SELFHARM = (r"suicid\w*|self-harm\w*|kill(?:ing)? (?:myself|herself|himself|themselves)|"
            r"end(?:ing)? (?:my|her|his|their) (?:own )?life|tak\w+ (?:my|her|his|their) (?:own )?life|"
            r"better off without|(?:want\w*|wish\w*) to die|not want\w* to (?:live|be here)")
METHOD = (r"overdos\w*|noose|hang(?:ing|ed)? (?:myself|herself|himself|themselves)|jump\w* (?:off|from|in front)|"
          r"shoot\w* (?:myself|herself|himself|themselves)|slit\w*|\bwrists?\b|carbon monoxide|poison\w*|"
          r"suffocat\w*|lethal|stockpil\w*|sav(?:ed|ing|e) up\b[^.]{0,20}(?:tablets|pills|medication)|"
          r"(?:crash|drive)\w* (?:the car )?(?:off|into)")
QTY = (r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|tablets?|pills?|capsules?|bottles?|boxes|packets?)\b|"
       r"\bhandful\b|\bwhole (?:bottle|box|packet)\b")
MEANS = r"firearm\w*|rifle\w*|\bguns?\b"
PROHIBIT = r"\b(?:never|do not|don't|does not|must not|should not|avoid\w*|without)\b"
DRUGS = r"tetrabenazine|deutetrabenazine|valbenazine|antidepressant|seizure medicine|olanzapine|risperidone|sertraline"
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def read(p):
    return p.read_text(encoding="utf-8") if p.exists() else ""


def strip_comments(text):
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))


def public_files(root, s):
    """Every file with scenario text: site content, the AI patient prompt, and the review checklists."""
    d = s["dir"]
    files = sorted(p for p in d.iterdir() if p.suffix in (".yaml", ".md"))
    prompt = root / "runtime" / "patient_prompts" / f"{d.name}.md"
    return files + ([prompt] if prompt.exists() else [])


def scenario_text(s):
    """Scenario text the numbers checks read; comments (citations, notes) and checklists are left out."""
    return "\n".join(strip_comments(read(p)) for p in sorted(s["dir"].iterdir())
                     if p.suffix in (".yaml", ".md") and not p.name.startswith("审核"))


def family_id(s):
    return s["card"]["scenario"].get("group") or "1"


def family_name(fid):
    return {"1": "Case 1", "A": "Case 2", "B": "Case 3", "C4": "Case 4", "C5": "Case 5"}.get(fid, fid)


def walk(node, key_suffix):
    """Yield values of dict keys ending in key_suffix, anywhere in a YAML tree."""
    if isinstance(node, dict):
        for k, v in node.items():
            if str(k).endswith(key_suffix) and isinstance(v, (str, int)):
                yield str(v)
            yield from walk(v, key_suffix)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v, key_suffix)


def people(card):
    who = [card.get("persona"), card.get("companion")] + list(card.get("others") or [])
    return [w for w in who if isinstance(w, dict) and w.get("name")]


def cag_pairs(text):
    found = re.findall(r"CAG[^.\n]{0,25}?\b(\d{1,3})\s*(?:/|and)\s*(\d{1,3})\b", text)
    return {tuple(sorted((int(a), int(b)))) for a, b in found}


def cag_singles(text):
    out = {int(x) for x in re.findall(r"\bCAG\s+(\d{1,3})\b(?!\s*/)", text)}
    out |= {int(x) for x in re.findall(r"(?<![-–\d])(?<!to )(?<!than )(?<![Oo]ver )(?<!above )\b(\d{2,3})\s+(?:CAG\s+)?repeats\b", text)}
    return out


def add(out, check, status, msg):
    out[check].append((status, msg))


# ---------------------------------------------------------------- risk tier
def risk_tier(s):
    card, cps = s["card"], s["cps"] or {}
    sc = card["scenario"]
    parts = [sc.get("title", ""), sc.get("trainee_brief", "")] + list(sc.get("learning_goals") or [])
    parts += [c.get("name", "") for c in cps.get("checkpoints", []) + cps.get("red_flags", [])]
    parts += re.findall(r"^#+ .*$", s["cards"], re.M)
    text = "\n".join(str(p) for p in parts)
    cats = [k for k, pat in RISK.items() if re.search(pat, text, re.I)]
    # Suicide also counts when it appears only in the mentor text or guided script.
    mentor = strip_comments(read(s["dir"] / "checkpoints.yaml")) + read(s["dir"] / "guided.yaml")
    if "suicide" not in cats and re.search(RISK["suicide"] + "|9-8-8", mentor, re.I):
        cats.insert(0, "suicide")
    ages = dict(card.get("ages_now") or {})
    ages.update({w["name"].split()[0]: w["age"] for w in people(card) if isinstance(w.get("age"), int)})
    minors = "|".join(n for n, a in ages.items() if a < 18)
    if minors and "minors testing" not in cats and re.search(rf"\b({minors})\b[^.]*\btest|\btest[^.]*\b({minors})\b", text):
        cats.append("minors testing")
    return ("high" if cats else "low"), cats


# ---------------------------------------------------------------- check 1
def check_numbers(s, out):
    text, card = scenario_text(s), s["card"]
    for a, b in cag_pairs(text):
        if a < CAG_MIN or b > CAG_MAX:
            add(out, 1, FAIL, f"CAG {a}/{b} is outside {CAG_MIN}-{CAG_MAX}")
        elif b < 36:
            add(out, 1, WARN, f"CAG {a}/{b}: neither allele is in the HD range")
        elif a >= 36:
            add(out, 1, WARN, f"CAG {a}/{b}: both alleles expanded (rare)")
    for line in re.split(r"[;\n]|\.\s", text):
        for m in re.finditer(r"\b(\d{2,3})\s+(?:CAG\s+)?repeats\b[^.]{0,40}?\b(normal|intermediate|reduced[- ]penetrance|full[- ]penetrance)", line, re.I):
            lo, hi = CAG_CATS[m.group(2).lower().replace("-", " ")]
            if not lo <= int(m.group(1)) <= hi:
                add(out, 1, FAIL, f"{m.group(1)} repeats called {m.group(2)} (range {lo}-{hi}): {line.strip()[:70]}")
        if re.search(r"\bCAG\b|repeat|penetrance|intermediate", line, re.I):
            for cat, (lo, hi) in CAG_CATS.items():
                for c in re.finditer(cat.replace(" ", "[- ]"), line, re.I):
                    ranges = [(max(r.start() - c.end(), c.start() - r.end(), 0), int(r.group(1)), int(r.group(2)))
                              for r in re.finditer(r"\b(\d{2})\s*(?:to|-|–)\s*(\d{2})\b", line)]
                    near = [r for r in ranges if r[0] <= 30]
                    if near:
                        _, a, b = min(near)
                        if (a, b) != (lo, hi):
                            add(out, 1, FAIL, f"{cat} stated as {a}-{b}, should be {lo}-{hi}: {line.strip()[:70]}")
    ages = dict(card.get("ages_now") or {})
    ages.update({w["name"].split()[0]: w["age"] for w in people(card) if w.get("age") is not None})
    for name, age in ages.items():
        if not isinstance(age, int) or not 0 <= age <= AGE_MAX:
            add(out, 1, FAIL, f"{name}: age {age} is not valid")
    for x in re.findall(r"\b(\d{1,3})-year-old\b", text):
        if int(x) > AGE_MAX:
            add(out, 1, FAIL, f"{x}-year-old is not valid")


def onset_check(members, results):
    """Onset type vs age and CAG for the affected person, using the family's earliest scenario."""
    first = members[0]["card"]
    canon = first.get("family_canonical") or {}
    who = canon.get("child_affected") or canon.get("patient")
    if who:
        name, cag = str(who).split()[0], next(walk(canon, "HTT_CAG"), "")
        age = next((m["card"]["ages_now"][name] for m in members if name in (m["card"].get("ages_now") or {})), None)
    else:   # Case 1: Teresa is the affected person; the age is at genetic confirmation
        name, age, cag = "Teresa", 52, next(walk(members[-1]["card"], "HTT_CAG"), "")
    large = max([int(x) for x in re.findall(r"\d+", cag)] or [0])
    joined = "\n".join(strip_comments(read(m["dir"] / "role_card.yaml")) for m in members)
    kind = "juvenile" if re.search(r"juvenile[- ]onset", joined, re.I) else \
        "late" if re.search(r"late[- ]onset", joined, re.I) else "adult"
    for m in members:
        out = results[m["dir"].name]
        lo, hi = ONSET[kind]
        if age is None:
            add(out, 1, WARN, f"no age found for affected person {name}")
            continue
        if not lo <= age <= hi:
            add(out, 1, FAIL, f"{kind} onset but {name} is {age} (expected {lo}-{hi})")
        c_lo, c_hi = ONSET_CAG[kind]
        if large and not c_lo <= large <= c_hi:
            add(out, 1, WARN, f"{kind} onset with CAG {large}: unusual, expected about {c_lo}-{c_hi}")


# ---------------------------------------------------------------- check 2
def attach(results, members, status, msg):
    names = [m["dir"].name for m in members if m["dir"].name in msg]
    for n in names or [m["dir"].name for m in members]:
        add(results[n], 2, status, msg)


def check_family(fid, members, results):
    if fid != "1":
        for _, name, probs in crc.check_group(fid, members):
            if "CAG" not in name:    # CAG is checked below for every family
                for p in probs or []:
                    attach(results, members, FAIL, f"{name}: {p}")
        months = [crc.months_after(m["card"]["scenario"]) for m in members]
        if any(b <= a for a, b in zip(months, months[1:])):
            attach(results, members, WARN, f"timeline: months_after not increasing ({months})")
    else:
        seen = {}
        for m in members:
            ppl = {w["name"].split()[0]: w["age"] for w in people(m["card"]) if w.get("age") is not None}
            text = scenario_text(m)
            mother = m["card"]["facts"].get("mother") or (m["card"]["facts"].get("carried_from_s1") or {}).get("mother")
            age = mother.get("age") if isinstance(mother, dict) else re.match(r"\d+", str(mother or ""))
            if age:     # s1 and s2 refer to Teresa only as Leah's mother
                ppl.setdefault("Teresa", age if isinstance(age, int) else int(age.group(0)))
            for name in list(seen) + list(ppl):
                for a in re.findall(rf"\b{name}, (\d{{1,3}})\b|\b{name} \((\d{{1,3}})\)", text):
                    ppl.setdefault(name, int(a[0] or a[1]))
            for name, age in ppl.items():
                if name in seen and not 0 <= age - seen[name] <= 1:
                    attach(results, [m], FAIL, f"{name} is {seen[name]} earlier, {age} in {m['dir'].name}")
                seen[name] = age
    lasts = [w["name"].split()[-1] for m in members for w in people(m["card"]) if len(w["name"].split()) > 1]
    canon_name = next((str(c["surname"]) for c in (m["card"].get("family_canonical") or {} for m in members) if c.get("surname")), None)
    family_surname = canon_name or (max(set(lasts), key=lasts.count) if lasts else None)
    first = {}
    for m in members:
        for w in people(m["card"]):
            parts = w["name"].split()
            if len(parts) > 1 and parts[-1] not in (family_surname or ""):    # the canonical line can name a kept surname
                attach(results, [m], WARN, f"{w['name']}: surname differs from family surname {family_surname}")
            if len(parts) > 1 and first.setdefault(parts[0], parts[-1]) != parts[-1]:
                attach(results, [m], FAIL, f"{parts[0]} has two surnames: {first[parts[0]]}, {parts[-1]}")
    canon_cag = set()
    for m in members:
        for v in walk(m["card"], "HTT_CAG"):
            canon_cag |= cag_pairs("CAG " + v)
    large = {b for _, b in canon_cag}
    for m in members:
        text = scenario_text(m)
        for a, b in sorted(cag_pairs(text) - canon_cag):
            attach(results, [m], FAIL, f"CAG {a}/{b} is not a canonical value in this family {sorted(canon_cag)}")
        for x in sorted(cag_singles(text) - large):
            attach(results, [m], WARN, f"CAG value {x} is not this family's expanded allele {sorted(large)}")
        ages = set()
        for x in members:     # any family member's age, so a parent's history in a child's scenario counts
            ages |= set((x["card"].get("ages_now") or {}).values()) | {w["age"] for w in people(x["card"]) if w.get("age")}
            ages |= {int(a) for a in re.findall(r"\b[A-Z][a-z]+, (\d{2})\b", scenario_text(x))}
        for raw in re.findall(r"(?:(\w+) years? ago[^.;\n]{0,30}?\bat (?:age )?(\d{2})\b)", text):
            n = WORDS.get(raw[0].lower()) or (int(raw[0]) if raw[0].isdigit() else None)
            if n and ages and n + int(raw[1]) not in ages:
                attach(results, [m], WARN, f"timeline: '{raw[0]} years ago at {raw[1]}' matches nobody's current age")
    last = {}
    for m in members:
        body = strip_comments(read(m["dir"] / "role_card.yaml"))
        now = {d.lower() for d in re.findall(rf"(?<!no )(?<!not on )\b({DRUGS})\b", body, re.I)}
        for drug in sorted(set(last) - now):
            attach(results, [m], WARN, f"medication: {drug} in {last[drug]} is not mentioned in {m['dir'].name}")
        last.update({d: m["dir"].name for d in now})


# ---------------------------------------------------------------- check 3
def parse_sources(root):
    """{key: text} from the comment headers of every checkpoints.yaml; definitions are merged."""
    blocks = {}
    for p in sorted((root / "scenarios").glob("*/checkpoints.yaml")):
        cur = []
        for line in read(p).splitlines():
            m = re.match(r"#\s+(s\d+(?:,\s*s\d+)*)\s*(=|\()", line)
            if m:
                cur = re.findall(r"s\d+", m.group(1))
                for k in cur:
                    blocks[k] = blocks.get(k, "") + " " + line.lstrip("# ")
            elif cur and re.match(r"#\s{3,}\S", line):
                for k in cur:
                    blocks[k] += " " + line.lstrip("# ")
            else:
                cur = []
    return blocks


def urls_in(text):
    urls = re.findall(r"https?://[!-~]+", re.sub(r"[;,)\]\"'<>]", " ", text))
    urls += ["https://doi.org/" + d for d in re.findall(r"\bdoi:(10\.[!-~]+?)(?=[\s;,)]|$|[^!-~])", text)]
    return sorted({u.rstrip(".:") for u in urls})


def cited_keys(s):
    keys = set()
    cps = s["cps"] or {}
    for c in cps.get("checkpoints", []) + cps.get("red_flags", []):
        keys |= set(crc.as_list(c.get("source")))
    for tag in re.findall(r"\[([^\]]+)\]", s["cards"]):
        keys |= set(re.findall(r"\bs\d+\b", tag))
    return keys


def check_required(s, out, sources, known, site, today, cats):
    for num, name, probs in crc.check_scenario(s, known):
        for p in probs or []:
            add(out, 3, FAIL, f"structure ({name}): {p}")
    for k in sorted(cited_keys(s), key=lambda x: int(x[1:])):
        b = sources.get(k, "")
        if not urls_in(b):
            add(out, 3, FAIL, f"{k} has no source URL")
        dates = re.findall(r"(?:verified|checked|reviewer|searched|accessed|read)[^.]{0,40}?(20\d\d-\d\d-\d\d)", b, re.I)
        if not dates:
            add(out, 3, FAIL, f"{k} has no check date")
        elif re.search(r"\b(act|code|law|trial|legislation)\b", b, re.I):
            age = (today - datetime.date.fromisoformat(max(dates))).days
            if age > STALE_DAYS:
                add(out, 3, WARN, f"{k}: law/trial source last checked {age} days ago")
        if re.search(r"needs? (?:human )?verification", b, re.I):
            add(out, 3, WARN, f"{k} still says it needs human verification")
    for p in sorted(s["dir"].glob("*")):
        if p.suffix in (".yaml", ".md") and "Reviewed by: PENDING" in read(p):
            add(out, 3, WARN, f"{p.name} still says Reviewed by: PENDING")
    prep = read(s["dir"] / "family_prep_sheet.md")
    if not re.search(r"not (?:legal or )?medical advice", prep, re.I):
        add(out, 3, FAIL, "family prep sheet has no 'not medical advice' disclaimer")
    if NOTICE not in site:
        add(out, 3, FAIL, "site page does not show the required notice")
    warning = s["card"]["scenario"].get("content_warning")
    if s["dir"].name in CONTENT_WARNING and not warning:
        add(out, 3, FAIL, "no content warning")
    if warning and warning.replace('"', "") not in site.replace("\\", ""):
        add(out, 3, FAIL, "content warning is not on the site page; rebuild it")
    if {"suicide", "safety"} & set(cats):
        text = "\n".join(read(s["dir"] / n) for n in ("role_card.yaml", "knowledge_cards.md", "family_prep_sheet.md", "guided.yaml"))
        if "9-8-8" not in text:
            add(out, 3, FAIL if "suicide" in cats else WARN, "no 9-8-8 in the scenario files")


# ---------------------------------------------------------------- check 4
def check_forbidden(root, s, out):
    for p in public_files(root, s):
        body = read(p)
        if p.suffix == ".yaml":
            body = strip_comments(body)
        for n, line in enumerate(body.splitlines(), 1):
            if line.lstrip().startswith("content_warning:"):    # the warning itself names the topic
                continue
            for sent in re.split(r"(?<=[.!?])\s+", line):
                method = re.search(METHOD, sent, re.I)
                harm = re.search(SELFHARM, sent, re.I)
                qty = re.search(QTY, sent, re.I)
                banned = re.search(PROHIBIT, sent, re.I)
                where = f"{p.name}: \"{sent.strip()[:80]}\""
                if harm and qty:
                    add(out, 4, FAIL, f"quantity with self-harm ({qty.group(0)}) in {where}")
                if method and harm and not banned:
                    add(out, 4, FAIL, f"method term ({method.group(0)}) in {where}")
                elif method and not banned:
                    add(out, 4, WARN, f"method term ({method.group(0)}), check the context in {where}")
                if harm and re.search(MEANS, sent, re.I) and not p.name.startswith("审核"):
                    add(out, 4, WARN, f"means of harm next to suicide wording; confirm no detail in {where}")


# ---------------------------------------------------------------- check 5
def probe(url):
    cmd = ["curl", "-s", "-o", "/dev/null", "-L", "--max-time", "25", "-A",
           "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36",
           "-w", "%{http_code}", url]
    code, rc = "000", 1
    for extra in ([], ["--http1.1"]):     # some government sites reset HTTP/2 requests from scripts
        r = subprocess.run(cmd + extra, capture_output=True, text=True)
        code, rc = r.stdout.strip() or "000", r.returncode
        if code.startswith(("2", "3")) or code in ("404", "410"):
            break
    if code.startswith(("2", "3")):
        return PASS, code
    if code in ("404", "410") or rc == 6:
        return FAIL, "DNS failure" if rc == 6 else code
    return WARN, code if code != "000" else f"no response (curl {rc})"


def scenario_urls(root, s, sources):
    urls = set()
    for k in cited_keys(s):
        urls |= set(urls_in(sources.get(k, "")))
    for p in s["dir"].iterdir():
        if p.name in ("family_prep_sheet.md", "knowledge_cards.md") or p.name.startswith("审核"):
            urls |= set(urls_in(read(p)))
    return urls


# ---------------------------------------------------------------- check 6
def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    if len(w) > 2 and w.endswith("e") and not w.endswith("le"):
        w = w[:-1]
    if w.endswith("ed") and len(w) > 3 and w[-3] not in "td":
        w = w[:-2]
    return max(1, len(re.findall(r"[aeiouy]+", w)))


def readability(text):
    """Return (Flesch-Kincaid grade, Flesch reading ease, words, sentences)."""
    lines = []
    for l in text.splitlines():
        l = re.sub(r"https?://\S+", "", l).strip()
        if not l or l.startswith(("Drafted by", "Educational only")):
            continue
        l = re.sub(r"^(#+|-|\*)\s*", "", l).replace("**", "")
        lines.append(l if re.search(r"[.!?:]$", l) else l + ".")
    sents = [x for x in re.split(r"(?<=[.!?:])\s+", " ".join(lines)) if re.search(r"[A-Za-z]", x)]
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", " ".join(sents))
    if not words:
        return None
    syl = sum(syllables(w) for w in words)
    wps, spw = len(words) / len(sents), syl / len(words)
    return round(0.39 * wps + 11.8 * spw - 15.59, 1), round(206.835 - 1.015 * wps - 84.6 * spw, 1), len(words), len(sents)


def check_readability(s, out):
    r = readability(read(s["dir"] / "family_prep_sheet.md"))
    if r is None:
        add(out, 6, FAIL, "no family prep sheet text")
        return None
    grade = r[0]
    status = PASS if grade <= READ_PASS else WARN if grade <= READ_WARN else FAIL
    add(out, 6, status, f"grade {grade}, reading ease {r[1]} ({r[2]} words, target grade {READ_PASS:g} or below)")
    return r


# ---------------------------------------------------------------- run and report
def worst(items, default=PASS):
    return max((x[0] for x in items), key=RANK.get, default=default)


def run(root, links, today):
    crc.SCEN = root / "scenarios"
    dirs = sorted(p for p in crc.SCEN.iterdir() if p.is_dir())
    picked = [crc.load(d) for d in dirs]
    results = {s["dir"].name: {c: [] for c in CHECKS} for s in picked}
    sources, known = parse_sources(root), crc.defined_sources()
    site = read(root / "web" / "hd_anchor_v2.html")
    meta, by_url = {}, {}
    for s in picked:
        name, out = s["dir"].name, results[s["dir"].name]
        tier, cats = risk_tier(s)
        meta[name] = {"tier": tier, "cats": cats, "family": family_id(s)}
        check_numbers(s, out)
        check_required(s, out, sources, known, site, today, cats)
        check_forbidden(root, s, out)
        check_readability(s, out)
        for u in scenario_urls(root, s, sources):
            by_url.setdefault(u, []).append(name)
    for fid in sorted({family_id(s) for s in picked}):
        members = [s for s in picked if family_id(s) == fid]
        members.sort(key=lambda m: crc.months_after(m["card"]["scenario"]))
        onset_check(members, results)
        check_family(fid, members, results)
    link_rows = []
    if links:
        with concurrent.futures.ThreadPoolExecutor(8) as ex:
            found = dict(zip(by_url, ex.map(probe, by_url)))
        for u, (status, detail) in sorted(found.items()):
            link_rows.append((status, detail, u, sorted(by_url[u])))
            if status != PASS:
                for n in by_url[u]:
                    add(results[n], 5, status, f"{detail}: {u}")
    for name, out in results.items():
        for c in out:
            out[c] = sorted(set(out[c]), key=lambda x: (-RANK[x[0]], x[1]))
        status = worst([x for c in out for x in out[c]])
        tier = meta[name]["tier"]
        meta[name]["status"] = status
        meta[name]["decision"] = ("BLOCKED: fix FAILs, then needs human review" if status == FAIL else "needs human review") \
            if tier == "high" else ("BLOCKED: fix FAILs" if status == FAIL else "review warnings" if status == WARN else "auto-pass")
    return results, meta, link_rows


def write_report(path, results, meta, link_rows, links, today):
    cell = lambda name, c: NA if c == 5 and not links else worst(results[name][c])
    L = ["# Publish check report", "",
         f"Generated by `scripts/check_publish_v1.py` on {today}. Do not edit by hand; re-run the script.", "",
         "This report checks consistency and required items. It does not show that content is clinically correct.",
         "High-risk scenarios can never auto-pass.", "",
         "## Summary", "",
         "| Scenario | Family | Risk | Why | " + " | ".join(f"{c} {n}" for c, n in CHECKS.items()) + " | Overall | Decision |",
         "|---|---|---|---|" + "---|" * len(CHECKS) + "---|---|"]
    for name in results:
        m = meta[name]
        L.append(f"| {name} | {family_name(m['family'])} | {m['tier']} | {', '.join(m['cats']) or '-'} | "
                 + " | ".join(cell(name, c) for c in CHECKS) + f" | {m['status']} | {m['decision']} |")
    L += ["", "## Findings by scenario", ""]
    for name, out in results.items():
        L += [f"### {name}", "", f"Risk: {meta[name]['tier']}. Decision: {meta[name]['decision']}.", ""]
        for c, title in CHECKS.items():
            items = [x for x in out[c] if x[0] != PASS or c == 6]
            if items:
                L.append(f"**{c} {title}**")
                L += [f"- {st}: {msg}" for st, msg in items]
                L.append("")
    L += ["## Source links", ""]
    if not links:
        L += ["Skipped (--no-links).", ""]
    else:
        counts = {st: sum(r[0] == st for r in link_rows) for st in (PASS, WARN, FAIL)}
        L += [f"{len(link_rows)} unique URLs: {counts[PASS]} reachable, {counts[WARN]} could not be verified, "
              f"{counts[FAIL]} broken. A 403, 429, 5xx or timeout usually means the site blocks scripts, not that "
              "the link is dead, so those are WARN and need a manual click.", "",
              "| Result | Code | URL | Used by |", "|---|---|---|---|"]
        L += [f"| {st} | {d} | {u} | {len(n)} scenario(s) |" for st, d, u, n in sorted(link_rows, key=lambda r: -RANK[r[0]]) if st != PASS]
        L.append("")
    L += ["## What this script cannot catch", "",
          "- Clinical accuracy, tone, or whether a statement matches its source.",
          "- Forbidden content in new wording: check 4 is a word-pattern search, so a clean result is not proof of safety.",
          "- A page that loads but no longer holds the cited content (link check tests reachability only).",
          "- Readability grades are estimates from a built-in syllable count; medical names such as Huntington raise them.", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--report")
    ap.add_argument("--no-links", action="store_true")
    a = ap.parse_args()
    root = pathlib.Path(a.root).resolve()
    today = datetime.date.today()
    results, meta, link_rows = run(root, not a.no_links, today)
    report = pathlib.Path(a.report) if a.report else root / "docs" / "publish_check_report.md"
    write_report(report, results, meta, link_rows, not a.no_links, today)
    print(f"{'Scenario':42}{'Risk':6}" + "".join(f"{c:6}" for c in CHECKS) + "Decision")
    for name in results:
        m = meta[name]
        row = "".join(f"{(NA if c == 5 and a.no_links else worst(results[name][c])):6}" for c in CHECKS)
        print(f"{name:42}{m['tier']:6}{row}{m['decision']}")
    print(f"\nReport: {report}")
    sys.exit(0 if all(m["decision"] == "auto-pass" for m in meta.values()) else 1)


if __name__ == "__main__":
    main()
