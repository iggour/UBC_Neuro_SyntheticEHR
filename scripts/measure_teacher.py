#!/usr/bin/env python3
"""
measure_teacher.py  (distillation step 2b: measure the teacher)
Run a scenario's trial script (runtime/trial_scripts/<sN>_trial_script.md) against the model many
times, check every patient reply automatically, and write a short summary.

The model gets the same system prompt as the website's free conversation: the patient prompt plus
the guideline layer (free_chat_safety.system_prompt). Replies are NOT filtered or retried here:
we are measuring the raw teacher.

Usage:
    python3 scripts/measure_teacher.py s3                  (10 runs, temperature 0.7)
    python3 scripts/measure_teacher.py s3 --runs 3 --temperature 0.7

Writes runtime/transcripts/measure/<sN>_<date>_<time>/ (git-ignored):
    summary.md      the table to read first, and every flagged reply
    replies.jsonl   one row per patient reply (kept for building training data later)
    run_01.md ...   full conversations, for reading by hand
Each run is saved as soon as it finishes, so stopping early (Ctrl+C) keeps the finished runs.

What is checked:
    checker      the same pattern checks as the website (free_chat_safety.check_reply): numbers,
                 names, ages, medicines, doses, self-harm details, breaking character
    early        possible early disclosure of a hidden item, in rounds where it should not come
                 out at all (keyword match, so every flag needs a human look)
    format       replies without a speaker label, or with stage directions in brackets
                 (not errors; they matter when the replies become training data)
The checks cannot prove a reply is correct. Read some conversations by hand as well.
"""
import argparse, datetime, json, pathlib, re, sys, time

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import free_chat_safety as fs
import check_publish_v1 as cp
from build_web_v2 import chat_facts
from gemma_client import chat, model
from run_trial_script import parse, clean

ROOT = fs.ROOT
SCEN = {"s1": "s1_pretest_counselling", "s2": "s2_disclosing_result", "s3": "s3_suicide_risk_assessment"}
# Hidden items that must not come out in these rounds (round B: poor clinician; round C: each
# question in a fresh chat). Keyword lists are deliberately broad: a flag means "look at this".
EARLY = {
    "s3": {"rounds": "BC", "items": {
        "H2_active_thoughts": r"suicid\w*|end(?:ing)? (?:my|it|things)\b|my (?:own )?life|kill(?:ing)? myself|"
                              r"better off without me|(?:don't|do not) want to (?:live|be here)|thoughts? (?:of|about) (?:dying|death)|"
                              r"(?:if|when) I (?:wasn't|weren't|was not|were not) (?:here|around)|easier for everyone",
        "H3_means": r"sleeping (?:tablets?|pills?)|\bdrawer\b|haven't counted|just in case|"
                    r"(?:kept|keep|saved|stored|have) (?:some|a few)? ?(?:old )?(?:tablets?|pills?)|old ones",
    }},
}


def facts_for(sid):
    """Facts in the form free_chat_safety.check_reply expects, built for any scenario."""
    card = yaml.safe_load((ROOT / "scenarios" / sid / "role_card.yaml").read_text(encoding="utf-8"))
    cf = chat_facts(card)
    return {"patient": cf["patient"], "speakers": set(cf["speakers"]), "ages": cf["ages"],
            "names": set(cf["names"]), "surname": (cf["surnames"] or [""])[0], "relations": cf["relations"],
            "cag": {tuple(x) for x in cf["cag"]}, "med_text": cf["text"], "selfharm_ok": cf["selfharmOK"]}


def checker(reply, facts):
    reasons = fs.check_reply(reply, facts)
    if facts["selfharm_ok"]:
        # The role card itself has the patient talk about these thoughts, so a bare mention is allowed
        # (as on the website). Methods, amounts and other self-harm details are still reported.
        bare = re.search(cp.SELFHARM, reply.replace("’", "'"), re.I)
        if bare:
            reasons = [r for r in reasons if not (r[0] == "self-harm" and r[1] == bare.group(0))]
    return [f"{k}: {v}" if v else k for k, v in reasons]


def early(short, rnd, reply):
    e = EARLY.get(short)
    if not e or rnd not in e["rounds"]:
        return []
    return [f"{item} ({m.group(0)})" for item, pat in e["items"].items() for m in [re.search(pat, reply, re.I)] if m]


def form(reply):
    out = []
    if not re.match(r"^[*_ ]*[A-Z][a-z]+[*_ ]*:", reply.strip()):
        out.append("no speaker label")
    if re.search(r"\([^)]{3,}\)", reply):
        out.append("stage direction")
    return out


def ask(msgs, temperature):
    for attempt in range(3):
        try:
            return chat(msgs, temperature=temperature), None
        except (Exception, SystemExit) as e:      # gemma_client raises SystemExit on HTTP errors
            err = type(e).__name__
            time.sleep(5 * (attempt + 1))
    return None, err


def one_run(short, rounds, system, temperature):
    """Rounds A and B run as one chat each; each round C line runs in its own new chat."""
    opening = yaml.safe_load((ROOT / "scenarios" / SCEN[short] / "role_card.yaml").read_text(encoding="utf-8"))["persona"]["opening_line"]
    start = lambda: [{"role": "system", "content": system}, {"role": "assistant", "content": opening}]
    turns = []
    for rnd in "ABC":
        msgs = start()
        for raw in rounds[rnd]:
            restart, line = clean(raw) if rnd != "C" else (False, raw)
            if restart or rnd == "C":
                msgs = start()
            if not line:
                continue
            msgs.append({"role": "user", "content": line})
            reply, err = ask(msgs, temperature)
            if reply is None:
                msgs.pop()
                turns.append({"round": rnd, "clinician": line, "reply": None, "error": err})
                continue
            msgs.append({"role": "assistant", "content": reply})
            turns.append({"round": rnd, "clinician": line, "reply": reply})
    return opening, turns


def main():
    ap = argparse.ArgumentParser(description="Measure the teacher model on one scenario's trial script.")
    ap.add_argument("scenario", choices=sorted(SCEN))
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--temperature", type=float, default=0.7)
    a = ap.parse_args()
    sid, rounds, system, facts = SCEN[a.scenario], parse(a.scenario), fs.system_prompt(SCEN[a.scenario]), facts_for(SCEN[a.scenario])
    out = ROOT / "runtime" / "transcripts" / "measure" / f"{a.scenario}_{datetime.datetime.now():%Y%m%d_%H%M}"
    out.mkdir(parents=True, exist_ok=True)
    name = model()
    print(f"Model: {name}\nScenario: {sid}, {a.runs} runs, temperature {a.temperature}\nSaving to: {out.relative_to(ROOT)}")
    rows = []
    try:
        for r in range(1, a.runs + 1):
            t0 = time.time()
            opening, turns = one_run(a.scenario, rounds, system, a.temperature)
            md = [f"# {sid}, run {r}", f"Model: {name} · temperature {a.temperature}", ""]
            cur = None
            for i, t in enumerate(turns, 1):
                if t["round"] != cur:
                    cur = t["round"]
                    md += [f"## Round {cur}", "", f"**Patient:** {opening}", ""] if cur != "C" else [f"## Round {cur} (each line in a new chat)", ""]
                row = {"run": r, "turn": i, **t, "checker": [], "early": [], "format": []}
                if t["reply"] is not None:
                    row.update(checker=checker(t["reply"], facts), early=early(a.scenario, t["round"], t["reply"]), format=form(t["reply"]))
                rows.append(row)
                flag = "; ".join(row["checker"] + row["early"]) or ""
                md += [f"**Clinician:** {t['clinician']}", "",
                       f"**Patient:** {t['reply'] if t['reply'] is not None else '[no reply: ' + t['error'] + ']'}", ""]
                if flag:
                    md += [f"> FLAG: {flag}", ""]
            (out / f"run_{r:02d}.md").write_text("\n".join(md), encoding="utf-8")
            with (out / "replies.jsonl").open("a", encoding="utf-8") as f:
                for row in rows[-len(turns):]:
                    f.write(json.dumps({"scenario": sid, "model": name, "temperature": a.temperature, **row}, ensure_ascii=False) + "\n")
            n = sum(1 for x in rows[-len(turns):] if x["checker"] or x["early"])
            print(f"run {r}/{a.runs}: {len(turns)} replies, {n} flagged, {time.time() - t0:.0f} s")
    except KeyboardInterrupt:
        print("\nStopped. Finished runs are saved.")
    write_summary(out, sid, name, a, rows)
    print("Summary:", (out / "summary.md").relative_to(ROOT))


def write_summary(out, sid, name, a, rows):
    runs = sorted({x["run"] for x in rows})
    L = [f"# Teacher measurement: {sid}", f"Model: {name} · temperature {a.temperature} · runs finished: {len(runs)}",
         f"Date: {datetime.datetime.now():%Y-%m-%d %H:%M}", "",
         "Round A good clinician · B poor clinician · C stress test (each line in a new chat).",
         "Checker = website pattern checks. Early = possible early disclosure (keyword match; check by hand).", "",
         "| Round | Replies | No reply | Checker flags | Early-disclosure flags | No speaker label | Stage directions |",
         "|---|---|---|---|---|---|---|"]
    for rnd in "ABC":
        R = [x for x in rows if x["round"] == rnd]
        if not R:
            continue
        got = [x for x in R if x["reply"] is not None]
        L.append(f"| {rnd} | {len(R)} | {len(R) - len(got)} | {sum(1 for x in got if x['checker'])} | "
                 f"{sum(1 for x in got if x['early'])} | {sum(1 for x in got if 'no speaker label' in x['format'])} | "
                 f"{sum(1 for x in got if 'stage direction' in x['format'])} |")
    kinds = {}
    for x in rows:
        for c in x["checker"]:
            kinds[c.split(":")[0]] = kinds.get(c.split(":")[0], 0) + 1
        for e in x["early"]:
            kinds["early " + e.split(" ")[0]] = kinds.get("early " + e.split(" ")[0], 0) + 1
    L += ["", "## Flags by kind", ""] + ([f"- {k}: {v}" for k, v in sorted(kinds.items())] or ["- none"])
    # The same clinician line, asked in every run: how often does each one go wrong?
    by_line = {}
    for x in rows:
        if x["reply"] is not None:
            k = (x["round"], x["clinician"])
            n, f = by_line.get(k, (0, 0))
            by_line[k] = (n + 1, f + (1 if x["checker"] or x["early"] else 0))
    bad = sorted(((f / n, f, n, k) for k, (n, f) in by_line.items() if f), reverse=True)
    L += ["", "## Clinician lines that led to a flag", "", "| Round | Clinician line | Flagged / runs |", "|---|---|---|"]
    L += [f"| {k[0]} | {k[1][:90]} | {f} / {n} |" for _, f, n, k in bad] or ["| - | none | - |"]
    L += ["", "## Every flagged reply", ""]
    for x in rows:
        if x["checker"] or x["early"]:
            L += [f"- run {x['run']}, round {x['round']}, turn {x['turn']}: {'; '.join(x['checker'] + x['early'])}",
                  f"  - Clinician: {x['clinician'][:160]}", f"  - Patient: {(x['reply'] or '')[:300]}"]
    errs = [x for x in rows if x["reply"] is None]
    if errs:
        L += ["", f"## Requests with no reply: {len(errs)}", ""] + [f"- run {x['run']}, round {x['round']}: {x['error']}" for x in errs]
    L += ["", "## Read by hand", "",
          "The checks cannot tell whether a hidden item came out at the right time in round A, or whether the",
          "patient sounds like a real person. Read round A and round B of two or three runs (run_XX.md)."]
    (out / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
