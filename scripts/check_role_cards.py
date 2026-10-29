#!/usr/bin/env python3
"""
check_role_cards.py

Consistency checker for scenario folders (role card + checkpoints + knowledge cards + guided mode).
check_consistency_v0.py checks a consult note against its Canonical Facts Sheet; it cannot read
role cards. This script fills that gap. It does NOT judge whether content is clinically correct.

Usage:
    python3 scripts/check_role_cards.py                 (all scenarios)
    python3 scripts/check_role_cards.py scenarios/A1_*  (some scenarios; family checks use the whole group)

Checks per scenario:
    1  Role card has the required fields; scenario.id matches the folder name
    2  Every hidden item has id, content and disclose_when; ids are unique
    3  Checkpoints: `unlocks` names a hidden item, `knowledge_card` names a card, every source key is defined
    4  Knowledge cards: every [sN] tag is defined
    5  Guided mode: checkpoints and red flags exist; each turn has exactly one best option; speakers are known
Checks per family group (scenario.group, e.g. A):
    6  family_canonical identical in every scenario of the group
    7  Ages: persona/companion/facts ages match ages_now; ages never go down and rise by no more than
       the years elapsed (months_after_A1, months_after_B1, ...); "Name, 14" / "Name (14)" / "14-year-old Name" in text match
    8  CAG pairs ("18 / 71", "CAG repeats of 18 and 71") in the group's files match family_canonical
"""
import math, pathlib, re, sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCEN = ROOT / "scenarios"
PASS, FAIL = "PASS", "FAIL"


def defined_sources():
    keys = set()
    for p in SCEN.glob("*/checkpoints.yaml"):
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r"#\s+(s\d+)\s*=", line)
            if m:
                keys.add(m.group(1))
    return keys


def as_list(x):
    return [] if x is None else (x if isinstance(x, list) else [x])


def load(d):
    y = lambda n: yaml.safe_load((d / n).read_text(encoding="utf-8")) if (d / n).exists() else None
    cards = (d / "knowledge_cards.md").read_text(encoding="utf-8") if (d / "knowledge_cards.md").exists() else ""
    return {"dir": d, "card": y("role_card.yaml"), "cps": y("checkpoints.yaml"), "guided": y("guided.yaml"),
            "cards": cards, "card_ids": set(re.findall(r"^## (\S+)", cards, re.M))}


def check_scenario(s, sources):
    out, card, d = [], s["card"], s["dir"]
    p = []
    for path in (("scenario", "id"), ("scenario", "title"), ("scenario", "trainee_brief"), ("persona", "name"),
                 ("persona", "age"), ("persona", "opening_line"), ("facts",), ("hidden",), ("behaviour_rules",)):
        node = card
        for k in path:
            node = node.get(k) if isinstance(node, dict) else None
        if node in (None, "", []):
            p.append("missing " + ".".join(path))
    if card.get("scenario", {}).get("id") != d.name:
        p.append(f"scenario.id '{card.get('scenario', {}).get('id')}' does not match folder '{d.name}'")
    out.append(("1", "Required role-card fields", p))

    p, hid = [], [h.get("id") for h in card.get("hidden", [])]
    for h in card.get("hidden", []):
        for k in ("id", "content", "disclose_when"):
            if not h.get(k):
                p.append(f"hidden item {h.get('id', '?')} has no {k}")
    if len(hid) != len(set(hid)):
        p.append("duplicate hidden ids")
    out.append(("2", "Hidden items complete", p))

    p, cps = [], s["cps"] or {}
    for c in cps.get("checkpoints", []) + cps.get("red_flags", []):
        if c.get("unlocks") and c["unlocks"] not in hid:
            p.append(f"{c['id']} unlocks unknown hidden item {c['unlocks']}")
        if c.get("knowledge_card") and c["knowledge_card"] not in s["card_ids"]:
            p.append(f"{c['id']} points to unknown knowledge card {c['knowledge_card']}")
        for k in as_list(c.get("source")):
            if k not in sources:
                p.append(f"{c['id']} cites undefined source {k}")
    out.append(("3", "Checkpoints link to hidden items, cards and sources", p))

    p = []
    for tag in re.findall(r"\[([^\]]+)\]", s["cards"]):
        for k in re.findall(r"s\d+", tag):
            if k not in sources:
                p.append(f"knowledge card cites undefined source {k}")
    out.append(("4", "Knowledge-card source tags defined", sorted(set(p))))

    g = s["guided"]
    if g is None:
        out.append(("5", "Guided mode consistent", None))
    else:
        p = []
        cp_ids = {c["id"] for c in cps.get("checkpoints", [])}
        rf_ids = {r["id"] for r in cps.get("red_flags", [])}
        names = {card["persona"]["name"].split()[0]}
        if card.get("companion"):
            names.add(card["companion"]["name"].split()[0])
        names |= {o["name"].split()[0] for o in card.get("others", [])}
        lines = list(g.get("opening", []))
        for t in g.get("turns", []):
            for c in as_list(t.get("checkpoint")):
                if c not in cp_ids:
                    p.append(f"{t['id']} uses unknown checkpoint {c}")
            best = [o for o in t.get("options", []) if o.get("quality") == "best"]
            if len(best) != 1:
                p.append(f"{t['id']} has {len(best)} best options")
            for o in t.get("options", []):
                if o.get("flag") and o["flag"] not in rf_ids:
                    p.append(f"{t['id']} uses unknown red flag {o['flag']}")
                lines += o.get("reply", [])
            lines += as_list(t.get("before")) + as_list(t.get("patient_asks"))
        for l in lines:
            m = re.match(r"^([A-Z][a-z]+):", l)
            if m and m.group(1) not in names:
                p.append(f"unknown speaker '{m.group(1)}' in: {l[:60]}")
        out.append(("5", "Guided mode consistent", sorted(set(p))))
    return out


def months_after(sc):
    """Months since the first scenario of the group (months_after_A1, months_after_B1, ...)."""
    return next((v for k, v in sc.items() if k.startswith("months_after_")), 0)


def all_text(s):
    d = s["dir"]
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(d.iterdir())
                     if p.suffix in (".yaml", ".md") and not p.name.startswith("审核"))


def check_group(group, members):
    out = []
    canon = [m["card"].get("family_canonical") for m in members]
    p = []
    for m, c in zip(members, canon):
        if c is None:
            p.append(f"{m['dir'].name}: no family_canonical")
        elif c != canon[0]:
            diff = sorted(k for k in set(c) | set(canon[0]) if c.get(k) != canon[0].get(k))
            p.append(f"{m['dir'].name}: family_canonical differs from {members[0]['dir'].name} in {diff}")
    out.append(("6", f"Group {group}: family facts identical", p))

    p = []
    rows = sorted(((months_after(m["card"]["scenario"]), m) for m in members), key=lambda r: r[0])
    for months, m in rows:
        ages, card, n = m["card"].get("ages_now") or {}, m["card"], m["dir"].name
        if not ages:
            p.append(f"{n}: no ages_now"); continue
        for role, who in [("persona", card.get("persona")), ("companion", card.get("companion"))] + \
                [("others", o) for o in card.get("others", [])]:
            if who and who.get("age") is not None:
                first = who["name"].split()[0]
                if first in ages and ages[first] != who["age"]:
                    p.append(f"{n}: {role} {first} age {who['age']}, ages_now says {ages[first]}")
        for k, v in (card.get("facts") or {}).items():
            if isinstance(v, dict) and "age" in v and k.capitalize() in ages and v["age"] != ages[k.capitalize()]:
                p.append(f"{n}: facts.{k}.age {v['age']}, ages_now says {ages[k.capitalize()]}")
        text = all_text(m)
        for name, age in ages.items():
            pats = [rf"\b{name}(?: \w+)?, (\d{{1,2}})\b", rf"\b{name}(?: \w+)? \((\d{{1,2}})\)",
                    rf"\b(\d{{1,2}})-year-old {name}\b", rf"\b{name}(?: \w+)? is (\d{{1,2}})\b"]
            for pat in pats:
                for a in re.findall(pat, text):
                    if int(a) != age:
                        p.append(f"{n}: text says {name} is {a}, ages_now says {age}")
    for (m0, a), (m1, b) in zip(rows, rows[1:]):
        a0, a1 = a["card"].get("ages_now") or {}, b["card"].get("ages_now") or {}
        span = math.ceil((m1 - m0) / 12) if m1 > m0 else 0
        for name in set(a0) & set(a1):
            gap = a1[name] - a0[name]
            if gap < 0 or gap > span:
                p.append(f"{name}: {a0[name]} at month {m0} -> {a1[name]} at month {m1} (allowed rise 0-{span})")
    out.append(("7", f"Group {group}: ages consistent", sorted(set(p))))

    p = []
    cag = (canon[0] or {}).get("child_affected_HTT_CAG", "")
    want = tuple(re.findall(r"\d+", str(cag)))
    for m in members:
        text = all_text(m)
        found = re.findall(r"\b(\d{2}) / (\d{2,3})\b", text) + re.findall(r"CAG repeats of (\d+) and (\d+)", text)
        for pair in found:
            if want and pair != want:
                p.append(f"{m['dir'].name}: CAG {pair[0]}/{pair[1]}, family_canonical says {'/'.join(want)}")
    out.append(("8", f"Group {group}: CAG numbers match", sorted(set(p))))
    return out


def show(title, results):
    print(f"\n== {title}")
    n = 0
    for num, name, probs in results:
        status = "N/A" if probs is None else (FAIL if probs else PASS)
        n += status == FAIL
        print(f"[{status}] Check {num}: {name}")
        for x in probs or []:
            print(f"        - {x}")
    return n


def main():
    dirs = [pathlib.Path(a).resolve() for a in sys.argv[1:]] or sorted(p for p in SCEN.iterdir() if p.is_dir())
    sources, fails = defined_sources(), 0
    picked = [load(d) for d in dirs]
    for s in picked:
        fails += show(s["dir"].name, check_scenario(s, sources))
    groups = sorted({s["card"]["scenario"].get("group") for s in picked} - {None})
    for gname in groups:
        members = [load(d) for d in sorted(p for p in SCEN.iterdir() if p.is_dir())]
        members = [m for m in members if m["card"]["scenario"].get("group") == gname]
        fails += show(f"family group {gname} ({len(members)} scenarios)", check_group(gname, members))
    print(f"\n{fails} check(s) failed.")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
