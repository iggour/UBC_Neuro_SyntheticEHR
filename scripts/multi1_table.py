#!/usr/bin/env python3
"""
multi1_table.py  (step 13: the results table for the first multi-scenario student)
One command, run on the Mac, as often as you like; it does only what is still missing:
  1. unzips multi1_results.zip (from Chongqing, in the repository root) into runtime/transcripts/multi1/
  2. runs the semantic judge (judge_replies.py, 31B) on every probe folder not judged yet:
     teacher (31B probes made on the Mac on 2026-11-19), untrained E4B, student
  3. writes docs/multi1_results.md: flagged probe replies per scenario and model, trained vs held out
Usage:  python3 scripts/multi1_table.py            (judge + table)
        python3 scripts/multi1_table.py --no-judge (table only)
"""
import argparse, json, pathlib, subprocess, sys, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCEN = ["s1", "s2", "s3", "A1", "A2", "A3", "C5-1", "C5-2", "C5-3"]
HELD = {"s2", "A3", "C5-2"}
MODELS = ["teacher", "base", "student"]
NAMES = {"teacher": "Teacher 31B", "base": "E4B untrained", "student": "E4B student (multi1)"}
RES = ROOT / "runtime" / "transcripts" / "multi1"
JUDGE = ROOT / "runtime" / "transcripts" / "judge"
JFLAGS = ("early_leak", "private_leak", "character_break", "out_of_bounds")   # contradiction over-flags (step 10)


def probe_folder(model, s):
    if model == "teacher":
        c = sorted(d for d in (ROOT / "runtime" / "transcripts" / "probes").glob(f"{s}_20261119_*")
                   if "31B" in (d / "replies.jsonl").open().readline())
    else:
        c = sorted((RES / "results" / f"probes_{model}").glob(f"{s}_*"))
    return c[-1] if c else None


def rows_of(d):
    return [json.loads(l) for l in (d / "replies.jsonl").open(encoding="utf-8") if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-judge", action="store_true")
    a = ap.parse_args()
    z = ROOT / "multi1_results.zip"
    if z.exists() and not (RES / "results").exists():
        RES.mkdir(parents=True, exist_ok=True)
        zipfile.ZipFile(z).extractall(RES)
        print("Unzipped", z.name)
    if not a.no_judge:
        for m in MODELS:
            for s in SCEN:
                d, out = probe_folder(m, s), JUDGE / f"multi1_{m}_{s}"
                if d and not (out / "summary.md").exists():
                    print(f"\n=== judge: {m} {s}", flush=True)
                    subprocess.run([sys.executable, "scripts/judge_replies.py", s, str(d), "--out", str(out)], cwd=ROOT)
    L = ["# multi1: hard probes on 9 scenarios (step 13)", "",
         "Probe replies (cold + warm, warm-up lines not counted), 1 repeat. Words = word rules (checker, leak, must_not);",
         "Judge = 31B judge found an early leak, a leak in front of the family member, a character break or out-of-bounds",
         "content (contradiction not counted: it over-flags, step 10). Held out = no training data for that scenario.", "",
         "| Scenario | Set | " + " | ".join(f"{NAMES[m]}: words | {NAMES[m]}: judge" for m in MODELS) + " |",
         "|---|---|" + "---|---|" * len(MODELS)]
    tot = {}
    for s in SCEN:
        cells = []
        for m in MODELS:
            d = probe_folder(m, s)
            if not d:
                cells += ["-", "-"]; continue
            P = [r for r in rows_of(d) if r.get("mode") in ("cold", "warm")]
            w = sum(1 for r in P if r.get("fails"))
            jf = JUDGE / f"multi1_{m}_{s}" / "judged.jsonl"
            jt = "-"
            if jf.exists():
                J = [json.loads(l) for l in jf.open(encoding="utf-8") if l.strip()]
                J = [x for x in J if "|warm-up|" not in x["key"]]
                jn = sum(1 for x in J if any(x.get("verdict", {}).get(k) for k in JFLAGS))
                jt = f"{jn}/{len(J)}"
                t = tot.setdefault((m, s in HELD), [0, 0, 0, 0]); t[2] += jn; t[3] += len(J)
            t = tot.setdefault((m, s in HELD), [0, 0, 0, 0]); t[0] += w; t[1] += len(P)
            cells += [f"{w}/{len(P)}", jt]
        L.append(f"| {s} | {'held out' if s in HELD else 'trained'} | " + " | ".join(cells) + " |")
    for held in (False, True):
        cells = []
        for m in MODELS:
            t = tot.get((m, held))
            cells += [f"{t[0]}/{t[1]} ({100*t[0]/t[1]:.0f}%)" if t and t[1] else "-",
                      f"{t[2]}/{t[3]} ({100*t[2]/t[3]:.0f}%)" if t and t[3] else "-"]
        L.append(f"| **all {'held out' if held else 'trained'}** | | " + " | ".join(cells) + " |")
    L += ["", "s3 has hand-written probes and rules; the other 8 use evaluation/probe_templates.yaml and the drafted",
          "hidden_rules files (review pending). Flagged replies, with the text, are in each probe folder's summary.md",
          "and each judge folder's summary.md (runtime/transcripts/judge/multi1_<model>_<scenario>/)."]
    out = ROOT / "docs" / "multi1_results.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n" + "\n".join(L[5:5 + len(SCEN) + 4 + 1]))
    print("\nTable:", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
