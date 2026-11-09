#!/usr/bin/env python3
"""
build_web_v2.py
Build the two websites from the reviewed scenario files, so the sites and the scenarios share one
source of truth. Re-run after changing any scenario file or either template.

Usage:  python3 scripts/build_web_v2.py
Reads:  scenarios/*/role_card.yaml, checkpoints.yaml, knowledge_cards.md, family_prep_sheet.md, guided.yaml (optional),
        mentor_notes.yaml (optional: key fact beside each mentor hint, copied from knowledge_cards.md)
        runtime/patient_prompts/*.md and the layer-3 guidelines (free conversation; see below)
        records/case*.yaml, records/shared_knowledge_cards.md, records/sources.yaml (Record tab, draft)
        Scenarios are listed by family (CASES below). Set a case's draft flag to label it as unreviewed.
Writes: site/clinicians/index.html   clinician training (scripts/web_v2_template.html)
        site/families/index.html     family prep sheets only (scripts/web_families_template.html)
        web/hd_anchor_v2.html        redirect from the old address to the home page
Never exported to the clinician page: mentor_only, met_if.
Free conversation (owner decision 2026-11-06): the patient prompt (runtime/patient_prompts/<id>.md, which
includes hidden items and behaviour rules) and the guideline layer are in the clinician page, because the
learner's browser sends them to the learner's own model. Anyone can read them in the page source.
The family page gets only family_prep_sheet.md content: no scenario, role card, mentor or source-list
data, so nothing for clinicians is in its source. scripts/check_families_site.py checks this.
"""
import json, pathlib, re, sys, yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import check_publish_v1 as cp
import free_chat_safety as fs

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCEN = ROOT / "scenarios"
RECORDS = ROOT / "records"
GROUP_CASE = {"B": 3, "C4": 4}      # records/*.yaml name their family by role-card group
TOPIC = {"s1": "Counselling before a predictive genetic test",
         "s2": "Giving a positive result",
         "s3": "Assessing suicide risk",
         "A1": "Telling parents their child has juvenile HD",
         "A2": "School, seizures and safety with a teenager",
         "A3": "Parents asking to test a healthy sibling",
         "B1": "An unexpected diagnosis later in life",
         "B2": "Driving and living independently",
         "B3": "A late-stage family meeting",
         "C4-1": "Recognising possible HD in primary care",
         "C4-2": "A diagnosis the patient does not see",
         "C4-3": "The partner alone: safety and a teenager's test",
         "C5-1": "Reproductive options for a gene carrier",
         "C5-2": "When HD starts: trials and research",
         "C5-3": "Work, insurance and genetic discrimination law"}
# The website lists scenarios by family ("case"), in this order. Folder names and scenario files are unchanged.
CASES = [
    {"n": 1, "name": "Leah's family", "draft": False, "shorts": ["s1", "s2", "s3"]},
    {"n": 2, "name": "Maya's family: juvenile-onset HD", "draft": False, "shorts": ["A1", "A2", "A3"]},
    {"n": 3, "name": "Ruth's family: late-onset HD", "draft": False, "shorts": ["B1", "B2", "B3"]},
    {"n": 4, "name": "Mark's family: behavioural onset, poor insight", "draft": False, "shorts": ["C4-1", "C4-2", "C4-3"]},
    {"n": 5, "name": "Kevin's family: from family planning to early symptoms", "draft": False, "shorts": ["C5-1", "C5-2", "C5-3"]},
]
# One-line description of the patient for each scenario, shown in the scenario picker.
DESC = {"s1": "Leah, 28 · at 50% risk, no symptoms · wants a predictive test",
        "s2": "Leah, 28 · no symptoms · positive predictive test result",
        "s3": "Teresa, 54 · adult-onset HD, early stage · low mood",
        "A1": "Maya, 14 · juvenile-onset HD, new diagnosis · talking with her parents",
        "A2": "Maya, 15 · juvenile-onset HD with new seizures · with her mother",
        "A3": "Owen, 10 · Maya's brother, no symptoms · parents ask for a test",
        "B1": "Ruth, 68 · late-onset HD, new diagnosis · no known family history",
        "B2": "Ruth, 70 · late-onset HD, mild to moderate stage · with her daughter",
        "B3": "Ruth, 75 · late-onset HD, late stage · meeting her family",
        "C4-1": "Mark, 45 · adopted, family history unknown · irritability and problems at work",
        "C4-2": "Mark, 45 · adult-onset HD, new diagnosis · says he has no symptoms",
        "C4-3": "Anna, 44 · Mark's wife, alone · conflict at home; daughter, 17, asks about testing",
        "C5-1": "Kevin, 34 · HD gene carrier (CAG 41), no symptoms · planning a family with Mei",
        "C5-2": "Kevin, 36 · early manifest HD · asks about clinical trials",
        "C5-3": "Kevin, 36 · early manifest HD · what to tell his employer and insurer"}

def parse_sources(path, store):
    key = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            break
        body = line[1:]
        m = re.match(r"\s+(s\d+)\s*=\s*(.*)", body)
        if m:
            key = m.group(1)
            store.setdefault(key, [])
            if len(store[key]) == 0:
                store[key] = [m.group(2).strip()]
            else:
                key = None          # first definition wins
            continue
        if key and re.match(r"\s{6,}\S", body):
            store[key].append(body.strip())
        else:
            key = None

def parse_cards(path):
    cards, cur = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            cid = line[3:].strip()
            cur = {"id": cid, "title": re.sub(r"\b(hd|cag|ai)\b", lambda m: m.group(1).upper(), cid.replace("-", " ").capitalize()), "points": []}
            cards.append(cur)
        elif cur and line.startswith("- "):
            cur["points"].append(line[2:].strip())
    return cards

def parse_prep(path):
    out = {"title": "", "subtitle": "", "note": "", "sections": []}
    sec = None
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("Drafted by"):
            continue
        if line.startswith("### "):
            sec = {"h": s[4:], "items": [], "checks": []}
            out["sections"].append(sec)
        elif line.startswith("## "):
            out["subtitle"] = s[3:]
        elif line.startswith("# "):
            out["title"] = s[2:]
        elif s.startswith("- [ ]") and sec is not None:
            sec["checks"].append(s[5:].strip())
        elif s.startswith("- ") and sec is not None:
            sec["items"].append(s[2:].strip())
        elif sec is None:
            out["note"] = (out["note"] + " " + s).strip()
    return out

def family_payload(sheets):
    """Prep sheets, plus support items and links gathered from them. Nothing else goes to the family page."""
    support, links = {}, {}
    for sh in sheets:
        for sec in sh["sections"]:
            for x in sec["items"] + sec["checks"]:
                for u in re.findall(r"https?://[^\s)>]+", x):
                    links.setdefault(u.rstrip(".,;"), []).append(sh["title"])
            if sec["h"].lower() == "support":
                # Crisis lines have their own box; one entry per link; placeholders without a link are left out.
                for x in sec["items"]:
                    url = re.search(r"https?://[^\s)>]+", x)
                    if not re.search(r"9-8-8|\b911\b|link to add", x):
                        support.setdefault(url.group(0) if url else x, x)
    return {"sheets": sheets, "support": list(support.values()),
            "links": [{"url": u, "sheets": sorted(set(t), key=t.index)} for u, t in links.items()]}

def key_facts(d, cards):
    """mentor_notes.yaml -> {checkpoint id: card point text}. Each text must still match its card point word for word."""
    p = d / "mentor_notes.yaml"
    if not p.exists():
        return {}
    by_id = {c["id"]: c["points"] for c in cards}
    out = {}
    for cid, n in (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("key_facts", {}).items():
        pts = by_id.get(n["card"], [])
        if n["point"] >= len(pts) or pts[n["point"]] != n["text"]:
            raise SystemExit(f"{d.name}/mentor_notes.yaml {cid}: text no longer matches {n['card']} point {n['point']}")
        out[cid] = n["text"]
    return out


def chat_facts(card):
    """Facts the page's reply checker needs (a port of free_chat_safety.load_facts that works for every scenario)."""
    first = lambda who: (str(who).split() or [""])[0]
    ppl = cp.people(card)
    patient = first(card["persona"]["name"])
    ages = dict(card.get("ages_now") or {first(w["name"]): w["age"] for w in ppl if w.get("age")})
    fam = card.get("family_canonical") or {}
    told = {k: card.get(k) for k in ("persona", "companion", "others", "facts", "hidden", "ages_now", "family_canonical")}
    dump = yaml.safe_dump(told, allow_unicode=True)
    known = yaml.safe_dump({k: card.get(k) for k in ("facts", "hidden", "family_canonical", "persona")}, allow_unicode=True)
    rel = {}
    if first(fam.get("patient", "")) == patient:
        for k in ("husband", "wife", "daughter", "son"):
            if isinstance(fam.get(k), str):
                rel[k] = first(fam[k])
    surnames = {str(w["name"]).split()[-1] for w in ppl if len(str(w["name"]).split()) > 1}
    if fam.get("surname"):
        surnames.add(first(fam["surname"]))
    for v in fam.values():          # e.g. "Mei Lin" when the wife kept her own surname
        for given, sur in re.findall(r"\b([A-Z][a-z]+) ([A-Z][a-z]+)\b", str(v)):
            if given in ages:
                surnames.add(sur)
    pairs = cp.cag_pairs(known)
    facts_text = yaml.safe_dump({k: card.get(k) for k in ("facts", "hidden")}, allow_unicode=True)
    return {"patient": patient, "speakers": sorted({first(w["name"]) for w in ppl}), "ages": ages,
            "names": sorted(set(re.findall(r"\b[A-Z][a-z]+\b", dump))), "surnames": sorted(surnames), "relations": rel,
            "cag": sorted(list(x) for x in pairs), "cagSingles": sorted(cp.cag_singles(known) | {b for _, b in pairs}),
            "text": facts_text.lower(), "selfharmOK": bool(re.search(cp.SELFHARM, facts_text, re.I))}


REDIRECT = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>HD Anchor</title>
<meta http-equiv="refresh" content="0; url=../index.html"><meta name="robots" content="noindex"></head>
<body><p>HD Anchor has moved. <a href="../index.html">Open HD Anchor</a>.</p></body></html>
"""

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(path.relative_to(ROOT), path.stat().st_size, "bytes")

def main():
    data, sources, draft_src, sheets = [], {}, [], []
    cards = [(d, yaml.safe_load((d / "role_card.yaml").read_text(encoding="utf-8")))
             for d in sorted(p for p in SCEN.iterdir() if p.is_dir())]
    order = {s: i for i, c in enumerate(CASES) for s in c["shorts"]}
    case_of = {s: c for c in CASES for s in c["shorts"]}
    cards.sort(key=lambda dc: (order.get(dc[0].name.split("_")[0], 99), dc[0].name))   # Case 1, then 2, then 3
    for d, card in cards:
        cps = yaml.safe_load((d / "checkpoints.yaml").read_text(encoding="utf-8"))
        known = set(sources)
        parse_sources(d / "checkpoints.yaml", sources)
        if card["scenario"].get("status") == "draft":
            draft_src += [k for k in sources if k not in known]
        sc, per = card["scenario"], card["persona"]
        short = sc["id"].split("_")[0]
        comp = card.get("companion")
        item = {
            "id": sc["id"], "short": short, "title": sc["title"], "topic": TOPIC.get(short, ""),
            "setting": sc["setting"], "brief": " ".join(sc["trainee_brief"].split()),
            "goals": [g if isinstance(g, str) else "; ".join(f"{k}: {v}" for k, v in g.items()) for g in sc["learning_goals"]],
            "patient": {"name": per["name"], "age": per.get("age"),
                        "opening": per["opening_line"],
                        "companion": ({"name": comp["name"], "relation": comp.get("relation", "")} if comp else None)},
            "cards": parse_cards(d / "knowledge_cards.md"),
            "checkpoints": [{"id": c["id"], "name": c["name"], "hint": c.get("hint", ""), "after": c.get("hint_after_turn"),
                             "met": c["feedback_met"],
                             "missed": c["feedback_missed"], "src": c.get("source"),
                             "card": c.get("knowledge_card")} for c in cps["checkpoints"]],
            "flags": [{"id": r["id"], "name": r["name"], "fb": r["feedback"], "src": r.get("source")}
                      for r in cps["red_flags"]],
            "guided": (yaml.safe_load((d / "guided.yaml").read_text(encoding="utf-8"))
                       if (d / "guided.yaml").exists() else None),
        }
        item["notes"] = key_facts(d, item["cards"])
        item["chat"] = {"prompt": (ROOT / "runtime" / "patient_prompts" / f"{sc['id']}.md").read_text(encoding="utf-8").strip(),
                        "facts": chat_facts(card)}
        case = case_of.get(short, {"n": 0, "draft": True})
        item.update({"case": case["n"], "desc": DESC.get(short, ""), "draft": case["draft"],
                     "warning": card["scenario"].get("content_warning", ""),
                     "month": next((v for k, v in sc.items() if k.startswith("months_after")), 0)})
        data.append(item)
        sheets.append({**parse_prep(d / "family_prep_sheet.md"), "draft": case["draft"]})
    records = {}
    for p in sorted(RECORDS.glob("case*.yaml")):
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        records[GROUP_CASE[doc["group"]]] = doc["reports"]
    known = set(sources)
    parse_sources(RECORDS / "sources.yaml", sources)
    draft_src += [k for k in sources if k not in known]
    src = {k: re.sub(r"\s*Status:.*$", "", " ".join(v)).strip() for k, v in sorted(sources.items(), key=lambda kv: int(kv[0][1:]))}
    guide = "\n\n".join([fs.GUIDELINE_NOTE] + [(ROOT / g).read_text(encoding="utf-8").strip() for g in fs.GUIDELINES] + [fs.FINAL_NOTE])
    payload = json.dumps({"scenarios": data, "sources": src, "guide": guide, "draftSources": draft_src, "records": records,
                          "recordCards": parse_cards(RECORDS / "shared_knowledge_cards.md"),
                          "cases": [{k: c[k] for k in ("n", "name", "draft")} for c in CASES]}, ensure_ascii=False).replace("</", "<\\/")
    fam = json.dumps(family_payload(sheets), ensure_ascii=False).replace("</", "<\\/")
    tpl = lambda name: (ROOT / "scripts" / name).read_text(encoding="utf-8")
    write(ROOT / "site" / "clinicians" / "index.html", tpl("web_v2_template.html").replace("/*__DATA__*/null", payload))
    write(ROOT / "site" / "families" / "index.html", tpl("web_families_template.html").replace("/*__DATA__*/null", fam))
    write(ROOT / "web" / "hd_anchor_v2.html", REDIRECT)
    print(len(data), "scenarios;", len(src), "sources;", len(sheets), "family sheets")

if __name__ == "__main__":
    main()
