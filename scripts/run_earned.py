#!/usr/bin/env python3
"""
run_earned.py  (phase 2: does the patient disclose a hidden item when the trainee earns it?)
Runs evaluation/<short>_earned_probes.yaml against the model at GEMMA_BASE_URL: each probe is a fresh
conversation (patient opening line, then the probe's steps one by one). Every reply is saved; the reply to
the last step is the one judged (judge_replies.py reads the "context" field). Held-out: never train on these.
Writes runtime/transcripts/earned/<short>_<date>_<time>/replies.jsonl and summary.md.
Usage:  python3 scripts/run_earned.py s1 --repeats 2
"""
import argparse, datetime, json, pathlib, sys, time

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import free_chat_safety as fs
from gemma_client import model
from measure_teacher import SCEN, facts_for, checker, ask

ROOT = fs.ROOT


def main():
    ap = argparse.ArgumentParser(description="Run the earned probes (disclosure when asked well).")
    ap.add_argument("scenario", choices=sorted(SCEN))
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--temperature", type=float, default=0.7)
    a = ap.parse_args()
    sid = SCEN[a.scenario]
    spec = yaml.safe_load((ROOT / "evaluation" / f"{a.scenario}_earned_probes.yaml").read_text(encoding="utf-8"))
    card = yaml.safe_load((ROOT / "scenarios" / sid / "role_card.yaml").read_text(encoding="utf-8"))
    opening, system, facts = card["persona"]["opening_line"], fs.system_prompt(sid), facts_for(sid)
    out = ROOT / "runtime" / "transcripts" / "earned" / f"{a.scenario}_{datetime.datetime.now():%Y%m%d_%H%M}"
    out.mkdir(parents=True, exist_ok=True)
    name, n_fail = model(), 0
    print(f"Model: {name}\nScenario: {sid}, {len(spec['probes'])} earned probes x {a.repeats} repeats\nSaving to: {out.relative_to(ROOT)}")
    t0 = time.time()
    for rep in range(1, a.repeats + 1):
        for p in spec["probes"]:
            msgs = [{"role": "system", "content": system}, {"role": "assistant", "content": opening}]
            ctx, reply = [], None
            for i, line in enumerate(p["steps"]):
                msgs.append({"role": "user", "content": line})
                reply, err = ask(msgs, a.temperature)
                if reply is None:
                    break
                msgs.append({"role": "assistant", "content": reply})
                if i < len(p["steps"]) - 1:
                    ctx += [["Trainee", line], ["Patient side", reply]]
            row = {"scenario": sid, "model": name, "temperature": a.temperature, "repeat": rep, "id": p["id"],
                   "target": p["target"], "category": "earned", "mode": "earned", "clinician": p["steps"][-1],
                   "reply": reply, "context": ctx, "checker": checker(reply, facts) if reply else ["no reply"]}
            n_fail += reply is None
            with (out / "replies.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    (out / "summary.md").write_text(f"# Earned probes: {sid}\nModel: {name} · repeats {a.repeats} · no reply: {n_fail}\n"
                                    "Disclosure is decided by judge_replies.py (target item revealed).\n", encoding="utf-8")
    print(f"done in {time.time() - t0:.0f} s, no reply: {n_fail}")


if __name__ == "__main__":
    main()
