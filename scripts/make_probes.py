#!/usr/bin/env python3
"""
make_probes.py  (multi-scenario run, 2026-11-19: held-out hard probes from shared templates)
Fills in evaluation/probe_templates.yaml for each scenario and writes evaluation/<short>_hard_probes.yaml,
the file run_probes.py reads and build_training_data.py keeps out of the training data.
s3 keeps its own hand-written file and is never overwritten; an existing file is only replaced with --force.

Usage:
    python3 scripts/make_probes.py s1 s2 A1 A2 A3 C5-1 C5-2 C5-3
    python3 scripts/make_probes.py A1 --force
"""
import argparse, pathlib, sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from measure_teacher import SCEN, ROOT
from make_conversations import pronouns, first_name


def fill(text, v):
    return text.format(**v) if isinstance(text, str) else text


def build(short):
    sid = SCEN[short]
    card = yaml.safe_load((ROOT / "scenarios" / sid / "role_card.yaml").read_text(encoding="utf-8"))
    tpl = yaml.safe_load((ROOT / "evaluation" / "probe_templates.yaml").read_text(encoding="utf-8"))
    comp = card.get("companion")
    v = dict(patient=first_name(card["persona"]["name"]), companion=first_name(comp["name"]) if comp else "", **pronouns(card))
    ok = lambda x: x.get("needs") is None or (x["needs"] == "companion") == bool(comp)
    warm = [fill(w["text"], v) for w in tpl["warm_up"] if ok(w)]
    probes = []
    for p in tpl["probes"]:
        if ok(p):
            probes.append({k: fill(val, v) for k, val in p.items() if k != "needs"})
    return sid, {"scenario": sid, "warm_up": warm, "probes": probes}


def main():
    ap = argparse.ArgumentParser(description="Write held-out hard probes for scenarios from the shared templates.")
    ap.add_argument("scenarios", nargs="+")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    for short in a.scenarios:
        if short == "s3":
            print("s3: skipped (hand-written file)"); continue
        out = ROOT / "evaluation" / f"{short}_hard_probes.yaml"
        if out.exists() and not a.force:
            print(f"{short}: exists, skipped (use --force)"); continue
        sid, spec = build(short)
        head = (f"# {short} hard probes: a HELD-OUT TEST SET for the simulated patient ({sid}).\n"
                "# NEVER use these lines, or the replies to them, as training data.\n"
                "# Made by scripts/make_probes.py from evaluation/probe_templates.yaml. Reviewed by: PENDING\n\n")
        out.write_text(head + yaml.safe_dump(spec, sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")
        print(f"{short}: {len(spec['probes'])} probes, {len(spec['warm_up'])} warm-up lines -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
