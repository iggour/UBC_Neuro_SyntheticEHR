#!/usr/bin/env python3
"""
make_earned_probes.py  (phase 2, 2026-11-20: does the patient open up when the trainee asks well?)
For every hidden item of a scenario, writes short scripted openings that EARN the item:
    two rapport lines -> (if the item is kept from someone in the room) ask that person to step out
    -> one good question from the item's tests_held.unlock_questions in evaluation/hidden_rules/<short>.yaml
(tests_held first: never shown to the teacher when the rules were drafted; tests_dev if needed). Two full
questions per item (topic labels without a question mark are skipped).
A correct patient discloses the target item in reply to the last line. run_earned.py runs them;
judge_replies.py decides whether the item came out. Like the hard probes, these lines are a held-out
test: build_training_data.py keeps them out of training data.
Writes evaluation/<short>_earned_probes.yaml (Reviewed by: PENDING).
Usage:  python3 scripts/make_earned_probes.py            (all 15 scenarios)
        python3 scripts/make_earned_probes.py s1 A2
"""
import pathlib, sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from measure_teacher import SCEN, ROOT
from make_conversations import first_name

N_Q = 2


def build(short):
    sid = SCEN[short]
    card = yaml.safe_load((ROOT / "scenarios" / sid / "role_card.yaml").read_text(encoding="utf-8"))
    rules = yaml.safe_load((ROOT / "evaluation" / "hidden_rules" / f"{short}.yaml").read_text(encoding="utf-8"))
    pat = first_name(card["persona"]["name"])
    comp = card.get("companion")
    hello = f"Hello {pat}" + (f", hello {first_name(comp['name'])}" if comp else "") + ". Thanks for coming in today."
    rapport = [hello, "Before we start, how have things been for you lately?"]
    probes = []
    for it in rules["items"]:
        cand = [" ".join(str(q).split()) for k in ("tests_held", "tests_dev")
                for q in ((it.get(k) or {}).get("unlock_questions") or [])]
        qs = [q for q in cand if q.endswith("?") and len(q.split()) >= 4][:N_Q]   # real questions; held-out ones first
        out = [f"{p}, would you mind stepping out for a few minutes so I can talk with {pat} on their own?"
               for p in (it.get("private_from") or [])]
        sp = first_name(it.get("speaker") or pat)
        for k, q in enumerate(qs, 1):
            q = " ".join(str(q).split())
            if sp != pat and sp.lower() not in q.lower():
                q = f"{sp}, {q[0].lower() + q[1:]}"           # put the question to the person who holds the item
            probes.append({"id": f"E-{it['id']}-{k}", "target": it["id"], "speaker": sp,
                           "steps": rapport + out + [q], "disclose_when": " ".join(str(it.get("disclose_when", "")).split())})
    return sid, {"scenario": sid, "probes": probes}


def main():
    shorts = sys.argv[1:] or sorted(SCEN)
    for short in shorts:
        sid, spec = build(short)
        out = ROOT / "evaluation" / f"{short}_earned_probes.yaml"
        head = (f"# {short} earned probes: a HELD-OUT TEST SET ({sid}). Never use as training data.\n"
                "# Made by scripts/make_earned_probes.py from evaluation/hidden_rules/" + short + ".yaml (tests_held). Reviewed by: PENDING\n\n")
        out.write_text(head + yaml.safe_dump(spec, sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")
        print(f"{short}: {len(spec['probes'])} earned probes")


if __name__ == "__main__":
    main()
