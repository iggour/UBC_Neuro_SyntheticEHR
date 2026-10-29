#!/usr/bin/env python3
"""
run_trial_script.py
Run the clinician lines from runtime/trial_scripts/<sN>_trial_script.md against the AI patient
and save the transcript for review against the five checks in README_试玩说明.md.
Usage:  python3 scripts/run_trial_script.py s3          (rounds A, B and C)
        python3 scripts/run_trial_script.py s3 A        (one round)
Round A and B lines run in one chat each. Each round C question runs in its own new chat.
Lines that are only a stage direction in brackets are skipped; a leading "(If ...)" note is removed;
"(Start a new chat)" starts a new chat.
"""
import re, sys
from gemma_client import ROOT
from patient_session import Session, save

def parse(short):
    p = ROOT / "runtime" / "trial_scripts" / f"{short}_trial_script.md"
    rounds, cur = {"A": [], "B": [], "C": []}, None
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^## Round ([ABC])\b", line)
        if m:
            cur = m.group(1); continue
        if line.startswith("## "):
            continue
        if cur in ("A", "B"):
            m = re.match(r"^\*\*\d+\.\*\*\s+(.*)$", line)
            if m:
                rounds[cur].append(m.group(1).strip())
        elif cur == "C":
            m = re.match(r"^- (.+)$", line)
            if m and re.search(r"[A-Za-z]{3}", m.group(1)) and not re.search(r"[一-鿿]", m.group(1)):
                rounds["C"].append(m.group(1).strip())
    c = []
    for q in rounds["C"]:
        q = re.sub(r"^Straight away[^:]*:\s*", "", q)        # keep only the line to say
        q = re.sub(r"\s*\((before|Assuming)[^)]*\)", "", q)
        if q.startswith("Ask "):
            continue                                       # instruction for a human tester
        c += [x.strip() for x in q.split(" / ") if x.strip()]
    rounds["C"] = c
    return rounds

def clean(line):
    restart = line.startswith("(Start a new chat)")
    line = re.sub(r"^\(Start a new chat\)\s*", "", line)
    line = re.sub(r"^\(If [^)]*\)\s*", "", line)
    line = re.sub(r"\s*\((Keep|before|Assuming)[^)]*\)", "", line)     # notes for the tester
    line = re.sub(r"^\((Assuming|Stay quiet|Pause)[^)]*\)\s*", lambda m: m.group(0) if m.group(1)!="Assuming" else "", line)
    if re.fullmatch(r"\([^)]*\)", line.strip()):
        return restart, None          # stage direction only
    return restart, line.strip()

def main():
    short = sys.argv[1] if len(sys.argv) > 1 else "s3"
    which = sys.argv[2].upper() if len(sys.argv) > 2 else "ABC"
    rounds, parts = parse(short), []
    for r in "AB":
        if r not in which: continue
        s = Session(short); print(f"\n=== Round {r} ===\n{s.name}: {s.opening}")
        for raw in rounds[r]:
            restart, line = clean(raw)
            if restart:
                s.restart(); print("--- new chat ---")
            if not line: continue
            print(f"\nYou: {line}\n{s.name}: {s.say(line)}")
        parts.append((f"Round {r}", s.log))
    if "C" in which:
        log = []
        print("\n=== Round C (each question in a new chat) ===")
        for q in rounds["C"]:
            s = Session(short); a = s.say(q)
            print(f"\nYou: {q}\n{s.name}: {a}")
            log += [("Note", "--- new chat ---"), ("Clinician", q), ("Patient", a)]
        parts.append(("Round C", log))
    print("\nSaved:", save(parts, short, "trial" + which))

if __name__ == "__main__":
    main()
