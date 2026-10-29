#!/usr/bin/env python3
"""
build_web_v2.py
Build web/hd_anchor_v2.html from the reviewed scenario files, so the website and the
scenarios share one source of truth. Re-run after changing any scenario file.

Usage:  python3 scripts/build_web_v2.py
Reads:  scenarios/*/role_card.yaml, checkpoints.yaml, knowledge_cards.md, family_prep_sheet.md, guided.yaml (optional)
Writes: web/hd_anchor_v2.html
Never exported to the page: hidden items, behaviour rules, mentor_only, met_if (patient/mentor only).
"""
import json, pathlib, re, yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCEN = ROOT / "scenarios"
TOPIC = {"s1": "Counselling before a predictive genetic test",
         "s2": "Giving a positive result",
         "s3": "Assessing suicide risk"}

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

def main():
    data, sources = [], {}
    for d in sorted(p for p in SCEN.iterdir() if p.is_dir()):
        card = yaml.safe_load((d / "role_card.yaml").read_text(encoding="utf-8"))
        cps = yaml.safe_load((d / "checkpoints.yaml").read_text(encoding="utf-8"))
        parse_sources(d / "checkpoints.yaml", sources)
        sc, per = card["scenario"], card["persona"]
        short = sc["id"].split("_")[0]
        comp = card.get("companion")
        data.append({
            "id": sc["id"], "short": short, "title": sc["title"], "topic": TOPIC.get(short, ""),
            "setting": sc["setting"], "brief": " ".join(sc["trainee_brief"].split()),
            "goals": [g if isinstance(g, str) else "; ".join(f"{k}: {v}" for k, v in g.items()) for g in sc["learning_goals"]],
            "patient": {"name": per["name"], "age": per.get("age"),
                        "opening": per["opening_line"],
                        "companion": ({"name": comp["name"], "relation": comp.get("relation", "")} if comp else None)},
            "cards": parse_cards(d / "knowledge_cards.md"),
            "checkpoints": [{"id": c["id"], "name": c["name"], "hint": c.get("hint", ""), "met": c["feedback_met"],
                             "missed": c["feedback_missed"], "src": c.get("source"),
                             "card": c.get("knowledge_card")} for c in cps["checkpoints"]],
            "flags": [{"id": r["id"], "name": r["name"], "fb": r["feedback"], "src": r.get("source")}
                      for r in cps["red_flags"]],
            "prep": parse_prep(d / "family_prep_sheet.md"),
            "guided": (yaml.safe_load((d / "guided.yaml").read_text(encoding="utf-8"))
                       if (d / "guided.yaml").exists() else None),
        })
    src = {k: re.sub(r"\s*Status:.*$", "", " ".join(v)).strip() for k, v in sorted(sources.items(), key=lambda kv: int(kv[0][1:]))}
    payload = json.dumps({"scenarios": data, "sources": src}, ensure_ascii=False).replace("</", "<\\/")
    tpl = (ROOT / "scripts" / "web_v2_template.html").read_text(encoding="utf-8")
    out = ROOT / "web" / "hd_anchor_v2.html"
    out.write_text(tpl.replace("/*__DATA__*/null", payload), encoding="utf-8")
    print(out, out.stat().st_size, "bytes;", len(data), "scenarios;", len(src), "sources")

if __name__ == "__main__":
    main()
