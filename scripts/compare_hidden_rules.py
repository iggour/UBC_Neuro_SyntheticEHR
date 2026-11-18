#!/usr/bin/env python3
"""
compare_hidden_rules.py  (distillation, all scenarios, step 1b: drafted rules vs the hand-written s3 rules)

Runs the hand-written s3 rules (make_conversations.py, run_probes.py, measure_teacher.py) and the drafted
rules (evaluation/hidden_rules/s3.yaml, from build_hidden_rules.py) over the saved s3 transcripts, counts
the flags of each, and lists every reply where the two disagree, for reading by hand. No model is called.

Checks (the same ones the s3 results used):
  conversations  runtime/transcripts/generate/s3_*: early disclosure per patient reply
                 (make_conversations.flag_turns: leak words before the unlocking question, or a private
                 item while Luis is in the room)
  probes         runtime/transcripts/probes/s3_*: leak words, for probes with "leak" in auto
  trial script   runtime/transcripts/measure/s3_*: rounds B and C, broad leak words (any match = early);
                 round A turns 5, 7, 9: did H1, H2, H3 come out where the script earns them (recall)
A disagreement is not an error of the drafted rules by itself: the hand rules have known false
positives too. Read the listed replies and decide which side is right.

Usage:  python3 scripts/compare_hidden_rules.py [--max-list 30]
Writes  runtime/transcripts/compare_rules/s3_<date>_<time>.md  (and disagreements.jsonl beside it)
"""
import argparse, collections, copy, datetime, json, pathlib, re, sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_hidden_rules as bh
import make_conversations as mc
import measure_teacher as mt
import run_probes as rp

ROOT = bh.ROOT
SHORT, SID = "s3", "s3_suicide_risk_assessment"
T = ROOT / "runtime" / "transcripts"
# Round A of the s3 trial script: turn that earns each item, and the words compare_measure.py counts
# (copied from compare_measure.py, which runs on import).
ROUND_A = {"H1_guilt_leah": (5, r"gave (?:this|it) to|my fault|blame myself"),
           "H2_active_thoughts": (7, r"\bthoughts?\b|\bI have\b|\bYes\b|thought about|wasn't here|better off|easier"),
           "H3_means": (9, r"drawer|sleeping (?:tablets|pills)")}
DEFLECT = r"I said I'm fine|Why are you asking"


def rule_sets():
    hand = {"unlock": mc.UNLOCK[SHORT], "early": mt.EARLY[SHORT]["items"], "leak": rp.LEAK[SHORT],
            "private": mc.PRIVATE[SHORT], "asked": mc.ASKED[SHORT]}
    a = bh.load_rules(SHORT)
    if a is None:
        raise SystemExit("evaluation/hidden_rules/s3.yaml not found: run build_hidden_rules.py s3 first")
    if len(a["private"]) > 1:
        print("note: more than one person in private; only the first is used")
    auto = {"unlock": a["unlock"], "early": a["early"], "leak": a["leak"],
            "private": a["private"][0] if a["private"] else None, "asked": a["asked"]}
    return {"hand": hand, "auto": auto}


ORIG = {}


def use(r):
    """Put one rule set into the modules that flag_turns reads (dicts changed in place)."""
    if not ORIG:
        ORIG.update(unlock=copy.deepcopy(mc.UNLOCK), early=copy.deepcopy(mt.EARLY), leak=copy.deepcopy(rp.LEAK),
                    private=copy.deepcopy(mc.PRIVATE), asked=copy.deepcopy(mc.ASKED))
    mc.UNLOCK[SHORT] = r["unlock"]
    mt.EARLY[SHORT] = {"rounds": "BC", "items": r["early"]}
    rp.LEAK[SHORT] = r["leak"]
    if r["private"]:
        mc.PRIVATE[SHORT] = r["private"]
    else:
        mc.PRIVATE.pop(SHORT, None)
    mc.ASKED[SHORT] = r["asked"]


def items_of(flags):
    return {f.split()[0] for f in flags}


def hits(patterns, text):
    t = (text or "").replace("’", "'")
    return {i for i, p in patterns.items() if p and re.search(p, t, re.I)}


def conversations(rs, facts):
    rows = []
    for d in sorted(T.glob(f"generate/{SHORT}_*")):
        f = d / "conversations.jsonl"
        if not f.exists():
            continue
        convs = [json.loads(l) for l in f.open(encoding="utf-8") if l.strip()]
        flags = {}
        for side, r in rs.items():
            use(r)
            flags[side] = [mc.flag_turns(SHORT, c["turns"], facts) for c in convs]
        for ci, c in enumerate(convs):
            for ti, t in enumerate(c["turns"]):
                if not t.get("reply"):
                    continue
                h, a = flags["hand"][ci][ti][1], flags["auto"][ci][ti][1]
                rows.append({"check": "conversations", "where": f"{d.name} conv {ci + 1} turn {t['turn']} ({c['type']})",
                             "clinician": t["clinician"], "reply": t["reply"], "hand": items_of(h), "auto": items_of(a),
                             "hand_words": h, "auto_words": a})
    return rows


def probe_ids():
    spec = yaml.safe_load((ROOT / "evaluation" / f"{SHORT}_hard_probes.yaml").read_text(encoding="utf-8"))
    out = {}
    def walk(x):
        if isinstance(x, dict):
            if "id" in x and "auto" in x:
                out[x["id"]] = x
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(spec)
    return {i for i, p in out.items() if "leak" in (p.get("auto") or [])}


def probes(rs):
    ids, rows = probe_ids(), []
    for d in sorted(T.glob(f"probes/{SHORT}_*")):
        for l in (d / "replies.jsonl").open(encoding="utf-8"):
            r = json.loads(l)
            if r.get("id") not in ids or not r.get("reply"):
                continue
            h, a = hits(rs["hand"]["leak"], r["reply"]), hits(rs["auto"]["leak"], r["reply"])
            rows.append({"check": "probes", "where": f"{d.name} {r['id']} {r.get('mode', '')} rep {r.get('repeat')}",
                         "clinician": r["clinician"], "reply": r["reply"], "hand": h, "auto": a})
    return rows


def trial(rs):
    early_rows, recall_rows = [], []
    affirm = mc.AFFIRM
    for d in sorted(T.glob(f"measure/{SHORT}_*")):
        for l in (d / "replies.jsonl").open(encoding="utf-8"):
            r = json.loads(l)
            if not r.get("reply"):
                continue
            where = f"{d.name} run {r['run']} {r['round']}{r['turn']}"
            if r["round"] in "BC":
                early_rows.append({"check": "trial B/C", "where": where, "clinician": r["clinician"], "reply": r["reply"],
                                   "hand": hits(rs["hand"]["early"], r["reply"]), "auto": hits(rs["auto"]["early"], r["reply"])})
            for item, (turn, pat) in ROUND_A.items():
                if r["round"] != "A" or r["turn"] != turn:
                    continue
                ok = not re.search(DEFLECT, r["reply"])
                h = ok and bool(re.search(pat, r["reply"], re.I))
                q = rs["auto"]["asked"].get(item)
                body = re.sub(r"\([^)]*\)|^[*_ ]*[A-Z][a-z]+[*_ ]*:", " ", r["reply"], flags=re.M)
                a = ok and bool(hits({item: rs["auto"]["leak"].get(item)}, r["reply"])
                                or (q and re.search(q, r["clinician"], re.I) and re.search(affirm, body, re.I)))
                recall_rows.append({"check": "trial A recall", "where": where, "item": item, "clinician": r["clinician"],
                                    "reply": r["reply"], "hand": {item} if h else set(), "auto": {item} if a else set()})
    return early_rows, recall_rows


def table(rows, items, title, recall=False):
    lines = [f"### {title} ({len(rows)} replies)", "",
             "| Item | Hand flags | Drafted flags | Both | Hand only | Drafted only |", "|---|---|---|---|---|---|"]
    for i in items:
        rr = [r for r in rows if r.get("item", i) == i]
        h = sum(i in r["hand"] for r in rr)
        a = sum(i in r["auto"] for r in rr)
        b = sum(i in r["hand"] and i in r["auto"] for r in rr)
        if recall:
            lines.append(f"| {i} (turn A{ROUND_A[i][0]}, {len(rr)} runs) | {h} | {a} | {b} | {h - b} | {a - b} |")
        else:
            lines.append(f"| {i} | {h} | {a} | {b} | {h - b} | {a - b} |")
    return lines + [""]


def listing(rows, max_list):
    out = []
    dis = [r for r in rows if r["hand"] != r["auto"]]
    for side, other, label in (("hand", "auto", "Hand only"), ("auto", "hand", "Drafted only")):
        sel = [r for r in dis if r[side] - r[other]]
        out += [f"#### {label}: {len(sel)} replies" + (f" (first {max_list})" if len(sel) > max_list else ""), ""]
        for r in sel[:max_list]:
            extra = ""
            if r.get("hand_words") is not None:
                extra = f" | hand: {r['hand_words']} | drafted: {r['auto_words']}"
            out += [f"- {r['where']}: **{', '.join(sorted(r[side] - r[other]))}**{extra}",
                    f"  - Clinician: {r['clinician']}",
                    "  - Reply: " + " / ".join(x.strip() for x in r["reply"].splitlines() if x.strip()), ""]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--max-list", type=int, default=30, help="replies listed per side and check")
    a = ap.parse_args()
    rs = rule_sets()
    facts = mt.facts_for(SID)
    conv = conversations(rs, facts)
    prob = probes(rs)
    tri_early, tri_recall = trial(rs)
    for k, v in ORIG.items():          # put the hand rules back
        {"unlock": mc.UNLOCK, "early": mt.EARLY, "leak": rp.LEAK, "private": mc.PRIVATE, "asked": mc.ASKED}[k].update(v)

    hand_items = sorted(set(rs["hand"]["leak"]) | set(rs["hand"]["unlock"]))
    all_items = sorted(set(rs["auto"]["leak"]) | set(hand_items))
    out_dir = T / "compare_rules"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = f"{datetime.datetime.now():%Y%m%d_%H%M}"
    md = out_dir / f"{SHORT}_{stamp}.md"
    y = yaml.safe_load((bh.OUT / f"{SHORT}.yaml").read_text(encoding="utf-8"))
    L = [f"# Drafted vs hand-written hidden-item rules, {SHORT}", "",
         f"Made {stamp} by scripts/compare_hidden_rules.py. Drafted rules: evaluation/hidden_rules/{SHORT}.yaml "
         f"({y['source']}, made {y['made']}; self-test failures: {y.get('dev_failures', y.get('self_test_failures'))} dev, "
         f"{y.get('held_failures', '-')} held out).",
         f"The hand rules cover {', '.join(hand_items)} only; flags for other items are new.", "",
         "## Counts", ""]
    L += table(conv, all_items, "Conversations: early disclosure (incl. private item with Luis in the room)")
    L += table(prob, all_items, "Probes: leak words")
    L += table(tri_early, all_items, "Trial script rounds B and C: broad leak words")
    L += table(tri_recall, list(ROUND_A), "Trial script round A: item came out where it is earned (recall)", recall=True)
    L += ["## Disagreements (read by hand)", ""]
    for title, rows in (("Conversations", conv), ("Probes", prob), ("Trial script B/C", tri_early),
                        ("Trial script A recall", tri_recall)):
        L += [f"### {title}", ""] + listing(rows, a.max_list)
    md.write_text("\n".join(L) + "\n", encoding="utf-8")
    with (out_dir / f"{SHORT}_{stamp}_disagreements.jsonl").open("w", encoding="utf-8") as f:
        for r in conv + prob + tri_early + tri_recall:
            if r["hand"] != r["auto"]:
                f.write(json.dumps({k: (sorted(v) if isinstance(v, set) else v) for k, v in r.items()},
                                   ensure_ascii=False) + "\n")
    print("\n".join(L[:L.index("## Disagreements (read by hand)")]))
    print(f"wrote {md.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
