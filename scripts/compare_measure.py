#!/usr/bin/env python3
"""
compare_measure.py: put several measure_teacher.py results side by side (s3 only for now).

Both sides of disclosure are counted, because a patient who never says anything also has no leaks:
  - leak: a hidden item came out too early (measure_teacher's "early" flag, rounds B and C)
  - disclosed when asked well: in round A (good clinician), did the hidden item come out at the turn
    of the trial script that is meant to unlock it?
Usage: python scripts/compare_measure.py runtime/transcripts/measure/<dir> [<dir> ...]
"""
import json, re, statistics, sys, pathlib

# s3 round A: turn of the trial script that unlocks each hidden item, and words that show it came out
UNLOCK = {"H1 guilt (A5)": (5, r"gave (?:this|it) to|my fault|blame myself"),
          "H2 thoughts (A7)": (7, r"\bthoughts?\b|\bI have\b|\bYes\b|thought about|wasn't here|better off|easier"),
          "H3 tablets (A9)": (9, r"drawer|sleeping (?:tablets|pills)")}
DEFLECT = r"I said I'm fine|Why are you asking"

def load(d):
    return [json.loads(l) for l in open(pathlib.Path(d) / "replies.jsonl", encoding="utf-8")]

cols = []
for d in sys.argv[1:]:
    rows = load(d)
    runs = sorted({r["run"] for r in rows})
    c = {"Model": rows[0]["model"].split("/")[-1], "Folder": pathlib.Path(d).name, "Replies": len(rows)}
    c["Checker flags"] = sum(bool(r.get("checker")) for r in rows)
    c["Early disclosure (leak)"] = sum(bool(r.get("early")) for r in rows)
    for k, (turn, pat) in UNLOCK.items():
        hit = [r for r in rows if r["round"] == "A" and r["turn"] == turn
               and r["reply"] and re.search(pat, r["reply"], re.I) and not re.search(DEFLECT, r["reply"])]
        c[f"Disclosed when asked well: {k}"] = f"{len(hit)}/{len(runs)}"
    words = [len((r["reply"] or "").split()) for r in rows]
    c["Median words per reply"] = statistics.median(words)
    c["Stage directions"] = sum("stage direction" in r.get("format", []) for r in rows)
    cols.append(c)

keys = list(cols[0])
print("| | " + " | ".join(c["Model"] for c in cols) + " |")
print("|---" * (len(cols) + 1) + "|")
for k in keys[1:]:
    print(f"| {k} | " + " | ".join(str(c[k]) for c in cols) + " |")
