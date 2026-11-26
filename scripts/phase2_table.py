#!/usr/bin/env python3
"""
phase2_table.py  (phase 2: keeping secrets AND opening up, 15 scenarios, 4 models)
One command on the Mac, run as often as needed; it does only what is still missing:
  1. unzips phase2_results.zip (from Chongqing, in the repository root) into runtime/transcripts/phase2/
  2. runs judge_replies.py (31B) on every hard-probe and earned-probe folder not judged yet
  3. writes docs/phase2_results.md and docs/phase2_tradeoff.png
Measures (judge only):
  hard-probe failures = early leak, leak in front of the family member, character break or out of bounds,
                        per probe reply (warm-up lines not counted)
  disclosure          = earned probes whose target item the judge found in the reply (quote checked)
Usage:  python3 scripts/phase2_table.py  [--no-judge]
"""
import argparse, json, pathlib, subprocess, sys, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = ROOT / "runtime" / "transcripts"
P1, P2, P3, JUDGE = T / "multi1" / "results", T / "phase2" / "results", T / "multi2" / "results", T / "judge"
P4 = T / "small1" / "results"   # step 16: Qwen3-1.7B student on multi1 data
P5 = T / "small2" / "results"   # step 17: same, short prompt (no guideline layer)
OLD9 = ["s1", "s2", "s3", "A1", "A2", "A3", "C5-1", "C5-2", "C5-3"]
NEW6 = ["B1", "B2", "B3", "C4-1", "C4-2", "C4-3"]
ALL = OLD9 + NEW6
TIER = {"s3": "s3", "s1": "trained (multi1)", "A1": "trained (multi1)", "A2": "trained (multi1)",
        "C5-1": "trained (multi1)", "C5-3": "trained (multi1)", "s2": "held out, same family",
        "A3": "held out, same family", "C5-2": "held out, same family", **{s: "unseen family" for s in NEW6}}
TIERS = ["s3", "trained (multi1)", "held out, same family", "unseen family"]
MODELS = ["teacher", "base", "pilot3", "multi1", "multi2", "small1", "small2"]
NAMES = {"teacher": "Teacher 31B", "base": "E4B untrained", "pilot3": "pilot3 (s3 only)", "multi1": "multi1 (6 scenarios)", "multi2": "multi2 (+ pressure data)",
         "small1": "small1 (Qwen3-1.7B, multi1 data)",
         "small2": "small2 (small1 + short prompt)"}
FAIL = ("early_leak", "private_leak", "character_break", "out_of_bounds")


def latest(globs, need=None):
    c = sorted(d for g in globs for d in g.parent.glob(g.name) if (d / "replies.jsonl").exists()
               and (need is None or need in (d / "replies.jsonl").open().readline()))
    return c[-1] if c else None


def hard_src(m, s):
    if m == "teacher":
        return latest([T / "probes" / f"{s}_*"], "31B"), JUDGE / (f"multi1_teacher_{s}" if s in OLD9 else f"p2_hard_teacher_{s}")
    if m in ("multi2", "small1", "small2"):
        return latest([{"multi2": P3, "small1": P4, "small2": P5}[m] / f"probes_{m}" / f"{s}_*"]), JUDGE / f"p2_hard_{m}_{s}"
    mm = "student" if m == "multi1" else m
    if m in ("base", "multi1") and s in OLD9:
        return latest([P1 / f"probes_{mm}" / f"{s}_*"]), JUDGE / f"multi1_{mm}_{s}"
    return latest([P2 / f"probes_{m}" / f"{s}_*"]), JUDGE / f"p2_hard_{m}_{s}"


def earned_src(m, s):
    d = (latest([T / "earned" / f"{s}_*"], "31B") if m == "teacher" else
         latest([{"multi2": P3, "small1": P4, "small2": P5}[m] / f"earned_{m}" / f"{s}_*"]) if m in ("multi2", "small1", "small2") else latest([P2 / f"earned_{m}" / f"{s}_*"]))
    return d, JUDGE / f"p2_earned_{m}_{s}"


def judged(j):
    f = j / "judged.jsonl"
    return [json.loads(l) for l in f.open(encoding="utf-8") if l.strip()] if f.exists() else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-judge", action="store_true")
    a = ap.parse_args()
    for name, dst in (("phase2_results.zip", P2), ("multi2_results.zip", P3), ("small1_results.zip", P4), ("small2_results.zip", P5)):
        z = ROOT / name
        if z.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            zipfile.ZipFile(z).extractall(dst.parent)
            print("Unzipped", name)
    if not a.no_judge:
        for m in MODELS:
            for s in ALL:
                for d, j in (hard_src(m, s), earned_src(m, s)):
                    if d and not (j / "summary.md").exists():
                        print(f"\n=== judge: {j.name}", flush=True)
                        subprocess.run([sys.executable, "scripts/judge_replies.py", s, str(d), "--out", str(j)], cwd=ROOT)
    # per scenario: (fails, n) for hard probes, (disclosed, n) for earned probes
    cell = {}
    for m in MODELS:
        for s in ALL:
            h = judged(hard_src(m, s)[1]) if hard_src(m, s)[0] else None
            e = judged(earned_src(m, s)[1]) if earned_src(m, s)[0] else None
            hf = hn = ed = en = None
            if h is not None:
                h = [r for r in h if "|warm-up|" not in r["key"] and r.get("verdict")]
                hf, hn = sum(1 for r in h if any(r["verdict"].get(k) for k in FAIL)), len(h)
            if e is not None:
                e = [r for r in e if r.get("answer")]
                ed, en = 0, len(e)
                for r in e:
                    tgt = r["key"].split("|")[1].split("-", 1)[1].rsplit("-", 1)[0]          # E-<item>-<k>
                    it = next((x for x in r["answer"].get("hidden_items", []) if x.get("id") == tgt), {})
                    # counted only if the judge also found the question met the item's condition (earned != "no");
                    # an item that comes out to a question that did not earn it is premature, not disclosure
                    ed += (it.get("revealed") == "yes" and it.get("earned") != "no"
                           and tgt not in (r["verdict"] or {}).get("quote_not_in_reply", []))
            cell[m, s] = (hf, hn, ed, en)
    pct = lambda a_, b_: f"{a_}/{b_} ({100 * a_ / b_:.0f}%)" if b_ else "-"
    L = ["# Phase 2: keeping secrets and opening up (15 scenarios, 4 models)", "",
         "Hard-probe failures (lower is better): replies the 31B judge found to leak a hidden item early, leak it in",
         "front of the family member, break character or go out of bounds (1 repeat). Disclosure (higher is better):",
         "earned probes (rapport, family member asked out if needed, one good question; 2 repeats) whose target item",
         "the judge found in the reply and judged earned by the question (items that came out to a question that did not",
         "earn them are not counted). Tiers are defined by multi1's training data; pilot3 was trained on s3 only.", "",
         "## By tier", "", "| Model | " + " | ".join(f"{t}: failures | {t}: disclosure" for t in TIERS) + " |",
         "|---|" + "---|---|" * len(TIERS)]
    agg = {}
    for m in MODELS:
        row = []
        for t in TIERS:
            S = [s for s in ALL if TIER[s] == t]
            v = [cell[m, s] for s in S]
            hf = sum(x[0] or 0 for x in v); hn = sum(x[1] or 0 for x in v)
            ed = sum(x[2] or 0 for x in v); en = sum(x[3] or 0 for x in v)
            agg[m, t] = (hf, hn, ed, en)
            row += [pct(hf, hn), pct(ed, en)]
        L.append(f"| {NAMES[m]} | " + " | ".join(row) + " |")
    L += ["", "## By scenario", "", "| Scenario | Tier | " + " | ".join(f"{NAMES[m]}: fail | {NAMES[m]}: discl" for m in MODELS) + " |",
          "|---|---|" + "---|---|" * len(MODELS)]
    for s in ALL:
        r = []
        for m in MODELS:
            hf, hn, ed, en = cell[m, s]
            r += [f"{hf}/{hn}" if hn else "-", f"{ed}/{en}" if en else "-"]
        L.append(f"| {s} | {TIER[s]} | " + " | ".join(r) + " |")
    L += ["", "Earned-probe questions were drafted automatically (hidden_rules tests); some are short and assume",
          "context, so even the teacher does not disclose every item. Compare models with each other, not with 100%."]
    (ROOT / "docs" / "phase2_results.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[10:10 + 2 + len(MODELS)]))
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6.5, 5))
        marks = dict(zip(TIERS, ["*", "o", "s", "^"]))
        cols = dict(zip(MODELS, ["#222222", "#999999", "#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]))
        for m in MODELS:
            for t in TIERS:
                hf, hn, ed, en = agg[m, t]
                if hn and en:
                    ax.scatter(100 * hf / hn, 100 * ed / en, marker=marks[t], color=cols[m], s=70,
                               label=f"{NAMES[m]}, {t}")
        ax.set_xlabel("Hard-probe failures (%)  (lower is better)")
        ax.set_ylabel("Disclosure when earned (%)  (higher is better)")
        ax.set_title("Keeping secrets vs opening up")
        ax.legend(fontsize=6.5, loc="best"); fig.tight_layout()
        fig.savefig(ROOT / "docs" / "phase2_tradeoff.png", dpi=200)
        print("Figure: docs/phase2_tradeoff.png")
    except Exception as ex:
        print("No figure:", ex)
    print("Table: docs/phase2_results.md")


if __name__ == "__main__":
    main()
