#!/usr/bin/env python3
"""
judge_validation.py  (agreement between the 31B judge and gold labels, phase 2 sample)
Reads evaluation/judge_validation/sample.json (100 replies, 25 per judge stratum, drawn with a fixed seed) and
labels.yaml (gold labels drafted by Claude without seeing the judge, checked by the owner). Writes
evaluation/judge_validation/results.md: agreement per stratum with Wilson 95% CIs, and the judge's
precision / negative predictive value for each probe type. Usage: python3 scripts/judge_validation.py
"""
import json, math, pathlib, yaml

R = pathlib.Path(__file__).resolve().parent.parent / "evaluation" / "judge_validation"


def wilson(x, n, z=1.96):
    p = x / n
    c = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    m = (p + z * z / (2 * n)) / (1 + z * z / n)
    return f"{x}/{n} = {100*p:.0f}% (95% CI {100*max(0, m-c):.0f}-{100*min(1, m+c):.0f})"


def main():
    s = json.loads((R / "sample.json").read_text(encoding="utf-8"))
    lab = yaml.safe_load((R / "labels.yaml").read_text(encoding="utf-8"))
    rows = {}
    for n, l in lab.items():
        j = s["judge"][l["key"]]
        rows.setdefault(j["stratum"], []).append((j["judge_says"], bool(l["label"]), int(n)))
    names = {"H+": "hard probe, judge: failure", "H-": "hard probe, judge: no failure",
             "E+": "earned probe, judge: disclosed", "E-": "earned probe, judge: not disclosed"}
    L = ["# Judge validation (phase 2, 14 non-s3 scenarios)", "",
         "100 replies drawn at random (seed 20261122), 25 from each judge verdict group. Gold labels drafted by Claude",
         "without seeing the judge's verdicts and checked by the first author (owner_check items). Agreement in the",
         "'judge: yes' groups is the judge's precision; in the 'judge: no' groups, its negative predictive value.", "",
         "| Group | Pool size | Agreement with gold |", "|---|---|---|"]
    tot = [0, 0]
    for k in ["H+", "H-", "E+", "E-"]:
        R_ = rows.get(k, [])
        a = sum(1 for j, g, _ in R_ if j == g); tot[0] += a; tot[1] += len(R_)
        L.append(f"| {names[k]} | {s['pool_sizes'][k]} | {wilson(a, len(R_))} |")
    L += [f"| **all** | | {wilson(*tot)} |", "", "Disagreements (number: judge -> gold):", ""]
    for k in ["H+", "H-", "E+", "E-"]:
        for j, g, n in sorted(rows.get(k, []), key=lambda r: r[2]):
            if j != g:
                L.append(f"- {n} ({names[k]}): judge {'yes' if j else 'no'}, gold {'yes' if g else 'no'}")
    (R / "results.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
