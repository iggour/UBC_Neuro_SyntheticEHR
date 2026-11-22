#!/usr/bin/env python3
"""
phase2_stats.py  (statistics for docs/phase2_results.md; no model calls, standard library only)
Reads the same judged files as phase2_table.py and writes docs/phase2_stats.md:
  1. every rate (hard-probe failures, disclosure when earned) per model and tier with a Wilson 95% CI
  2. differences between models, pooled over scenario groups, with a 95% CI and two-sided p from a
     cluster bootstrap that resamples SCENARIOS (replies within a scenario are not independent), 10,000 draws
Scenario groups: all 15; seen by multi1 (s3 + its 5 other training scenarios); new to multi1 (3 held out +
6 unseen-family scenarios). s3 alone has one cluster, so it gets Wilson CIs but no bootstrap test.
Usage:  python3 scripts/phase2_stats.py
"""
import json, math, pathlib, random, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import phase2_table as pt

B = 10000
GROUPS = {"all 15 scenarios": pt.ALL,
          "seen by multi1 (6)": [s for s in pt.ALL if pt.TIER[s] in ("s3", "trained (multi1)")],
          "new to multi1 (9)": [s for s in pt.ALL if pt.TIER[s] in ("held out, same family", "unseen family")]}
PAIRS = [("pilot3", "multi1"), ("multi1", "multi2"), ("teacher", "multi1"), ("teacher", "multi2"),
         ("base", "multi1"), ("base", "pilot3")]


def counts(m, s):
    """(fails, n_hard, disclosed, n_earned) for model m, scenario s (same rules as phase2_table)."""
    hd, hj = pt.hard_src(m, s)
    ed, ej = pt.earned_src(m, s)
    h = pt.judged(hj) if hd else None
    e = pt.judged(ej) if ed else None
    f = n = d = k = 0
    if h:
        h = [r for r in h if "|warm-up|" not in r["key"] and r.get("verdict")]
        f, n = sum(1 for r in h if any(r["verdict"].get(x) for x in pt.FAIL)), len(h)
    if e:
        e = [r for r in e if r.get("answer")]
        k = len(e)
        for r in e:
            tgt = r["key"].split("|")[1].split("-", 1)[1].rsplit("-", 1)[0]
            it = next((x for x in r["answer"].get("hidden_items", []) if x.get("id") == tgt), {})
            d += (it.get("revealed") == "yes" and it.get("earned") != "no"
                  and tgt not in (r["verdict"] or {}).get("quote_not_in_reply", []))
    return f, n, d, k


def wilson(x, n, z=1.96):
    if not n:
        return None
    p = x / n
    c = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    mid = (p + z * z / (2 * n)) / (1 + z * z / n)
    return p, max(0.0, mid - c), min(1.0, mid + c)


def fmt(x, n):
    w = wilson(x, n)
    return "-" if w is None else f"{100*w[0]:.0f}% ({100*w[1]:.0f}-{100*w[2]:.0f}) {x}/{n}"


def rate(C, m, S, kind):
    a = sum(C[m, s][0 if kind == "fail" else 2] for s in S)
    b = sum(C[m, s][1 if kind == "fail" else 3] for s in S)
    return a / b if b else float("nan")


def boot(C, m1, m2, S, kind, rng):
    obs = rate(C, m2, S, kind) - rate(C, m1, S, kind)
    ds = []
    for _ in range(B):
        R = [rng.choice(S) for _ in S]
        ds.append(rate(C, m2, R, kind) - rate(C, m1, R, kind))
    ds = sorted(d for d in ds if not math.isnan(d))
    lo, hi = ds[int(0.025 * len(ds))], ds[int(0.975 * len(ds)) - 1]
    p = min(1.0, 2 * min(sum(d <= 0 for d in ds), sum(d >= 0 for d in ds)) / len(ds))
    return obs, lo, hi, p


def main():
    rng = random.Random(20261122)
    C = {(m, s): counts(m, s) for m in pt.MODELS for s in pt.ALL}
    L = ["# Phase 2 statistics", "", "Made by scripts/phase2_stats.py from the judged files behind docs/phase2_results.md.",
         "Rates with Wilson 95% confidence intervals. Differences: cluster bootstrap over scenarios (10,000 draws),",
         "95% percentile interval and two-sided p. Failures: hard probes (lower is better). Disclosure: earned probes",
         "(higher is better). Replies within a scenario are correlated, so tests resample whole scenarios.", "",
         "## 1. Rates by tier", ""]
    for kind, title in (("fail", "Hard-probe failures"), ("disc", "Disclosure when earned")):
        L += [f"### {title}", "", "| Model | " + " | ".join(pt.TIERS) + " |", "|---|" + "---|" * len(pt.TIERS)]
        for m in pt.MODELS:
            row = []
            for t in pt.TIERS:
                S = [s for s in pt.ALL if pt.TIER[s] == t]
                i, j = (0, 1) if kind == "fail" else (2, 3)
                row.append(fmt(sum(C[m, s][i] for s in S), sum(C[m, s][j] for s in S)))
            L.append(f"| {pt.NAMES[m]} | " + " | ".join(row) + " |")
        L.append("")
    L += ["## 2. Differences between models (second minus first, percentage points)", ""]
    for kind, title in (("fail", "Hard-probe failures"), ("disc", "Disclosure when earned")):
        L += [f"### {title}", "", "| Comparison | " + " | ".join(GROUPS) + " |", "|---|" + "---|" * len(GROUPS)]
        for m1, m2 in PAIRS:
            row = []
            for g, S in GROUPS.items():
                o, lo, hi, p = boot(C, m1, m2, S, kind, rng)
                row.append(f"{100*o:+.1f} ({100*lo:+.1f} to {100*hi:+.1f}), p={p:.3f}" if p >= 0.001
                           else f"{100*o:+.1f} ({100*lo:+.1f} to {100*hi:+.1f}), p<0.001")
            L.append(f"| {pt.NAMES[m2]} vs {pt.NAMES[m1]} | " + " | ".join(row) + " |")
        L.append("")
    L += ["Notes: s3 is a single scenario and is included in 'all' and 'seen by multi1' but not tested alone.",
          "Hard probes: 1 repeat per model; earned probes: 2 repeats. A p-value below 0.05 with an interval that",
          "excludes 0 is read as a difference; wide intervals mean the data cannot separate the models."]
    out = pt.ROOT / "docs" / "phase2_stats.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[8:]))


if __name__ == "__main__":
    main()
