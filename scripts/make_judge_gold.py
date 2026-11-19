#!/usr/bin/env python3
"""
make_judge_gold.py  (distillation, step 10: gold labels for checking the judge, s3)

  python3 scripts/make_judge_gold.py candidates   -> evaluation/judge_gold/s3_candidates.jsonl
  python3 scripts/make_judge_gold.py merge        -> evaluation/judge_gold/s3_gold.jsonl

candidates: a fixed, seeded selection of s3 replies (with their context, as judge_replies.py sees them):
  known      replies whose truth was read by hand in steps 3-8 (flags at generation or test time in the
             batches named in distillation_log.md), the F4 false-premise replies from before the fix, and
             false-premise replies from pilot3
  rules      replies where the hand-written and the drafted word rules disagree (compare_hidden_rules.py)
             plus a sample where both flag
  disclose   trial-script round A turns 5, 7, 9 (the item is earned there; should not be a leak)
  random     replies no rule flagged, spread over the batches (to see whether the judge over-flags)
merge: joins the candidates with the hand labels in evaluation/judge_gold/s3_labels.yaml
  (key -> early_leak [ids], private_leak [ids], contradiction, character_break, out_of_bounds, note,
  owner_check). Rows without a label are left out and listed.
"""
import collections, json, pathlib, random, re, sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import judge_replies as jr

ROOT = jr.ROOT
T = ROOT / "runtime" / "transcripts"
G = ROOT / "evaluation" / "judge_gold"
SID = "s3_suicide_risk_assessment"
SEED = 10

# Batches whose flags were read by hand (distillation_log.md steps 3, 6, 7, 8)
KNOWN_GENERATE = ["s3_20261112_1538", "s3_20261112_1626", "s3_20261116_1001", "s3_20261118_1241"]
KNOWN_PROBES = ["s3_20261112_1506", "s3_20261119_0310", "s3_20261119_0544"]
KNOWN_MEASURE = ["s3_20261114_0700", "s3_20261119_0546"]


def flagged_in_file(d):
    """keys of replies flagged when they were made (saved checker / early / fails fields)."""
    out = {}
    if (d / "conversations.jsonl").exists():
        for n, l in enumerate((d / "conversations.jsonl").open(encoding="utf-8"), 1):
            c = json.loads(l)
            for t in c["turns"]:
                f = (t.get("checker") or []) + (t.get("early") or [])
                if t.get("reply") and f:
                    out[f"generate/{d.name}|conv {n}|turn {t['turn']}"] = f
    else:
        for l in (d / "replies.jsonl").open(encoding="utf-8"):
            r = json.loads(l)
            f = (r.get("checker") or []) + (r.get("early") or []) + (r.get("fails") or [])
            if not r.get("reply") or not f:
                continue
            if "round" in r:
                out[f"measure/{d.name}|run {r['run']}|{r['round']}{r['turn']}"] = f
            else:
                out[f"probes/{d.name}|{r['id']}|{r.get('mode')}|rep {r.get('repeat')}"] = f
    return out


def compare_keys():
    """Disagreements and agreements of the hand and drafted rules, from the latest compare run."""
    f = sorted((T / "compare_rules").glob("s3_*_disagreements.jsonl"))[-1]
    dis = {}
    for l in f.open(encoding="utf-8"):
        r = json.loads(l)
        if r["check"] != "conversations":
            continue
        m = re.match(r"(\S+) conv (\d+) turn (\d+)", r["where"])
        dis[f"generate/{m.group(1)}|conv {m.group(2)}|turn {m.group(3)}"] = f"hand {r['hand']} / drafted {r['auto']}"
    return dis, f.name


def candidates():
    rng = random.Random(SEED)
    opening = jr.load_card(SID)["persona"]["opening_line"]
    rows = {}
    for kind in ("generate", "probes", "measure"):
        for d in sorted((T / kind).glob("s3_*")):
            for r in jr.load_folder(d, opening):
                rows[r["key"]] = r
    pick = collections.OrderedDict()

    def add(key, why):
        if key in rows and key not in pick:
            pick[key] = why

    flagged = {}
    for name in KNOWN_GENERATE:
        flagged.update(flagged_in_file(T / "generate" / name))
    for name in KNOWN_PROBES:
        flagged.update(flagged_in_file(T / "probes" / name))
    for name in KNOWN_MEASURE:
        flagged.update(flagged_in_file(T / "measure" / name))
    for k, f in flagged.items():
        if "/s3_20261112_1506|" in k and not re.search(r"\|(J3|J4|F4)\|", k):
            continue                                   # old teacher probes: only the groups the log describes
        add(k, "known: flagged when made: " + "; ".join(f)[:200])

    dis, fname = compare_keys()
    for k, why in dis.items():
        add(k, f"rules: {why} ({fname})")

    for k in [k for k, r in rows.items() if k.startswith("measure/s3_20261119_0546|") and re.search(r"\|A(5|7|9)$", k)][:12]:
        add(k, "disclose: round A turn where the item is earned")

    all_flagged = set()
    for kind in ("generate", "probes", "measure"):
        for d in sorted((T / kind).glob("s3_*")):
            all_flagged |= set(flagged_in_file(d))
    pool = [k for k in rows if k not in pick and k not in all_flagged and k not in dis and k.startswith("generate/")]
    rng.shuffle(pool)
    for k in pool[:50]:
        add(k, "random: generated conversation, no flag")
    ppool = [k for k in rows if k not in pick and k not in all_flagged and (k.startswith("probes/") or k.startswith("measure/"))]
    rng.shuffle(ppool)
    for k in ppool[:20]:
        add(k, "random: probe or trial script, no flag")
    # added after the random draw, so the random sample does not change
    for k in rows:                                     # log step 3: before the fix the teacher agreed to the
        if re.match(r"probes/s3_20261112_1506\|F4\|", k):  # invented hospital stay (F4) in 6 of 6 replies
            add(k, "known: F4 before the fix (log step 3: agreed to an invented event 6/6)")
    for k in [k for k in rows if re.match(r"probes/s3_20261119_0544\|F[1-4]\|", k)][:8]:
        add(k, "known: false-premise probes after the fix (pilot3)")

    G.mkdir(parents=True, exist_ok=True)
    with (G / "s3_candidates.jsonl").open("w", encoding="utf-8") as f:
        for k, why in pick.items():
            f.write(json.dumps({**rows[k], "why": why}, ensure_ascii=False) + "\n")
    c = collections.Counter(w.split(":")[0] for w in pick.values())
    print(f"{len(pick)} candidates: {dict(c)} -> {(G / 's3_candidates.jsonl').relative_to(ROOT)}")


def merge():
    cands = [json.loads(l) for l in (G / "s3_candidates.jsonl").open(encoding="utf-8")]
    labels = yaml.safe_load((G / "s3_labels.yaml").read_text(encoding="utf-8")) or {}
    out, missing = [], []
    for c in cands:
        lab = labels.get(c["key"])
        if lab is None:
            missing.append(c["key"])
            continue
        gold = {"early_leak": lab.get("early_leak") or [], "private_leak": lab.get("private_leak") or [],
                "contradiction": bool(lab.get("contradiction")), "character_break": bool(lab.get("character_break")),
                "out_of_bounds": bool(lab.get("out_of_bounds"))}
        out.append({**c, "gold": gold, "note": lab.get("note", ""), "owner_check": bool(lab.get("owner_check"))})
    with (G / "s3_gold.jsonl").open("w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(out)} gold rows -> {(G / 's3_gold.jsonl').relative_to(ROOT)}; {len(missing)} candidates without a label")
    for k in missing[:20]:
        print("  no label:", k)


if __name__ == "__main__":
    {"candidates": candidates, "merge": merge}[sys.argv[1] if len(sys.argv) > 1 else "candidates"]()
