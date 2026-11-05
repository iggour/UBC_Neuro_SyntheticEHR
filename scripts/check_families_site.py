#!/usr/bin/env python3
"""
check_families_site.py
After build_web_v2.py: confirm that the family site holds no clinician-only data, even in the page
source, and that the entry pages are wired as intended. Run it after every build.

Usage:
    python3 scripts/check_families_site.py

FAIL  (must be fixed before publishing)
    - role card, checkpoint, mentor or guided-mode field names anywhere in the family page source
    - words that name clinician-only material ("hidden", "checkpoint", "red flag", "mentor", ...) in its text or data
    - any link from the family page to the clinician site or the old combined page
    - eight or more words in a row copied from patient data (role cards outside the scenario block, synthetic records), except
      crisis-line wording; links are ignored
    - names of the fictional patients and families
    - entry pages: clinician page without noindex, gate checkbox, family button or 9-8-8 / 911;
      home page that does not lead with the family site
REVIEW (listed for a person to judge; not an error by itself)
    - sensitive words in family text: suicide, self-harm, weapons, prognosis, juvenile HD, late stage,
      death. Lines that are crisis-line support notes (9-8-8 / 911) are counted separately.
    - eight or more words in a row shared with teaching text (checkpoints, guided mode, knowledge cards):
      or a role card's scenario block: usually the same question or fact written for both audiences
"""
import html, json, pathlib, re, sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
FAM = ROOT / "site" / "families" / "index.html"
CLIN = ROOT / "site" / "clinicians" / "index.html"
HOME = ROOT / "index.html"
# Field names from role_card.yaml, checkpoints.yaml, guided.yaml and the clinician page data.
FIELDS = ["persona", "companion", "disclose_when", "behaviour_rules", "mentor_only", "met_if", "feedback_met",
          "feedback_missed", "red_flags", "checkpoints", "trainee_brief", "trainee_role", "learning_goals",
          "opening_line", "emotional_baseline", "family_canonical", "ages_now", "expected_questions",
          "if_pressed_or_lectured", "knowledge_card", "patient_asks", "months_after", "content_warning",
          "recordCards", "draftSources", '"hidden"', '"guided"', '"flags"', '"brief"', '"goals"']
WORDS = [r"hidden", r"checkpoints?", r"red flags?", r"mentor", r"role[- ]cards?", r"trainee", r"scenarios?",
         r"guided", r"free conversation", r"simulated patient", r"for clinicians"]
SENSITIVE = {"suicide / self-harm": r"suicid\w*|self-harm\w*|end(?:ing)? (?:their|your|his|her|my) (?:own )?life|"
                                    r"not (?:wanting|want) to (?:live|be here)|kill\w*|overdos\w*",
             "weapons / violence": r"firearms?|weapons?|guns?|violen\w*|abus\w*|unsafe",
             "prognosis / death": r"prognos\w*|life expectancy|end of life|dying|\bdeath\b|\bdie[sd]?\b",
             "juvenile HD": r"juvenile",
             "late stage": r"late[- ]stage|feeding tube"}
CRISIS = r"9-8-8|\b911\b"
SHINGLE = 8
PLACES = {"Calgary", "Kamloops", "Ontario", "Vancouver", "Victoria"}
# The scenario block of a role card (brief, learning goals) is teaching text; everything else is patient data.
PATIENT_DATA = r"role_card\.yaml:(?!scenario\b)|records/"


def family_text(page):
    """Visible text and every string in the page data, one item per line."""
    data = json.loads(re.search(r"var D=(\{.*?\});\n", page, re.S).group(1).replace("<\\/", "</"))
    strings = []

    def walk(x):
        if isinstance(x, dict):
            strings.extend(x.keys())
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, str):
            strings.append(x)
    walk(data)
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S)
    visible = [html.unescape(t).strip() for t in re.split(r"<[^>]+>", body)]
    return [t for t in visible + strings if t]


def clinician_strings():
    out = []

    def walk(x, where):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, f"{where}:{k}" if where.endswith("role_card.yaml") else where)
        elif isinstance(x, list):
            for v in x:
                walk(v, where)
        elif isinstance(x, str):
            out.append((x, where))
    for d in sorted(p for p in (ROOT / "scenarios").iterdir() if p.is_dir()):
        for name in ("role_card.yaml", "checkpoints.yaml", "guided.yaml"):
            if (d / name).exists():
                walk(yaml.safe_load((d / name).read_text(encoding="utf-8")), f"{d.name}/{name}")
        out += [(l, f"{d.name}/knowledge_cards.md") for l in (d / "knowledge_cards.md").read_text(encoding="utf-8").splitlines()]
    # Review checklists (审核清单) are internal notes about these same files, so they are left out.
    for p in sorted((ROOT / "records").glob("*.yaml")) + sorted((ROOT / "records").glob("[!审]*.md")):
        if p.suffix == ".yaml":
            walk(yaml.safe_load(p.read_text(encoding="utf-8")), f"records/{p.name}")
        else:
            out += [(l, f"records/{p.name}") for l in p.read_text(encoding="utf-8").splitlines()]
    return out


def shingles(text):
    w = re.findall(r"[a-z0-9']+", re.sub(r"https?://\S+", " ", text).lower())
    return {" ".join(w[i:i + SHINGLE]) for i in range(len(w) - SHINGLE + 1)}


def people():
    names = set()
    for d in (ROOT / "scenarios").iterdir():
        if not (d / "role_card.yaml").exists():
            continue
        card = yaml.safe_load((d / "role_card.yaml").read_text(encoding="utf-8"))
        for w in [card.get("persona"), card.get("companion")] + list(card.get("others") or []):
            if isinstance(w, dict) and w.get("name"):
                names.add(str(w["name"]).split()[0])
        names |= set((card.get("ages_now") or {}).keys())
        canon = yaml.safe_dump(card.get("family_canonical") or {})
        names |= set(re.findall(r"\b[A-Z][a-z]{2,}\b", canon)) - PLACES
    return names


def main():
    page, clin, home = (p.read_text(encoding="utf-8") for p in (FAM, CLIN, HOME))
    fails, review, support, shared = [], {}, [], []
    texts = family_text(page)
    content = "\n".join(texts)

    for f in FIELDS:
        if re.search(rf"(?<![\w-]){re.escape(f)}(?![\w-])", page):
            fails.append(f"field name {f} in the page source")
    for w in WORDS:
        for m in re.finditer(rf"\b{w}\b", content, re.I):
            line = content[content.rfind("\n", 0, m.start()) + 1:content.find("\n", m.end())]
            fails.append(f"word '{m.group(0)}' in: {line[:110]}")
    # Any address of the clinician site, written in any form (markup, page data, script), counts as a link.
    for m in re.finditer(r"[\w./:-]*(?:clinicians?/|hd_anchor_v2|iggour\.github\.io)[\w./-]*", page, re.I):
        fails.append(f"link or address {m.group(0)}")
    clin_shingles = {}
    for text, where in clinician_strings():
        for s in shingles(text):
            clin_shingles.setdefault(s, where)
    for t in texts:
        if re.search(CRISIS, t):
            continue
        hit = sorted({clin_shingles[s] for s in shingles(t) if s in clin_shingles})
        patient = [h for h in hit if re.search(PATIENT_DATA, h)]
        if patient:
            fails.append(f"copied from {', '.join(patient)}: {t[:100]}")
        elif hit:
            shared.append(f"{t[:100]}  [also in {', '.join(hit)}]")
    names = people()
    for t in texts:
        for n in sorted(names):
            if re.search(rf"\b{n}\b", t):
                fails.append(f"fictional name '{n}' in: {t[:100]}")
    for t in texts:
        for label, pat in SENSITIVE.items():
            if re.search(pat, t, re.I):
                (support if re.search(CRISIS, t) else review.setdefault(label, [])).append(t)

    # Entry pages
    for need, what in ((r'<meta name="robots" content="noindex">', "noindex"),
                       (r"I am a healthcare professional or student", "gate checkbox"),
                       (r"I am a patient or family member – take me to the family pages", "family button"),
                       (r'href="\.\./families/index\.html"', "family link"), (r"9-8-8", "9-8-8"), (r"911", "911")):
        if not re.search(need, clin):
            fails.append(f"clinician page: {what} missing")
    if not re.search(r'id="gateok" disabled', clin):
        fails.append("clinician page: Continue is not disabled until the box is ticked")
    links = re.findall(r'href="([^"]+)"', home)
    if not links or links[0] != "site/families/index.html":
        fails.append(f"home page: first link is {links[:1]}, not the family site")
    for l in links:
        if not (ROOT / l).exists():
            fails.append(f"home page: link {l} has no page")

    print(f"Family site: {FAM} ({len(page)} bytes, {len(texts)} text items)")
    print(f"Checked against {len(clin_shingles)} {SHINGLE}-word phrases from clinician-only files and {len(names)} names:")
    print("  " + ", ".join(sorted(names)) + "\n")
    print(f"FAIL: {len(fails)}")
    for f in fails:
        print("  -", f)
    print(f"\nREVIEW: sensitive words outside crisis-line notes ({sum(len(v) for v in review.values())} lines)")
    for label, items in review.items():
        print(f"  {label}:")
        for t in dict.fromkeys(items):
            print("    -", t[:150])
    print(f"\nREVIEW: wording shared with teaching text ({len(set(shared))} distinct lines)")
    for t in dict.fromkeys(shared):
        print("    -", t)
    print(f"\nCrisis-line support notes with sensitive words (expected): {len(set(support))} distinct lines")
    for t in dict.fromkeys(support):
        print("    -", t[:150])
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
