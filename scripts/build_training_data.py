#!/usr/bin/env python3
"""
build_training_data.py  (distillation step 4b: turn practice conversations into training examples)
Reads the conversations made by make_conversations.py and writes chat-format training examples:
patient instructions + the conversation so far  ->  the patient's next reply.

Usage:
    python3 scripts/build_training_data.py runtime/transcripts/generate/s3_20261112_1538
    python3 scripts/build_training_data.py FOLDER [FOLDER ...] --max-repeats 3 --valid 0.1

Rules, in this order, for each conversation:
    1. Stop the conversation at the first reply that is missing or fails a check (checker or early
       disclosure, recomputed with today's rules). Later turns are dropped: their history contains it.
    2. Stop the conversation at a clinician line that is close to a held-out probe or warm-up line
       (evaluation/<sN>_hard_probes.yaml), so no exam question reaches the training data.
    3. Every reply is rewritten to one format: "Name: (stage direction) words", one line per speaker.
       The history the model sees is rewritten the same way.
    4. A reply whose words (ignoring stage directions) have already been kept --max-repeats times is
       not used as a target again (it stays in the history of later turns).
Conversations are split into train and valid by conversation, never by turn.

Writes runtime/transcripts/training_data/<sN>_<date>_<time>/ (git-ignored):
    train.jsonl, valid.jsonl   {"messages": [...], "meta": {...}} per line; the last message is the target
    report.md                  counts by rule and by trainee type, the most repeated replies, samples
The system prompt is the one in use now (free_chat_safety.system_prompt), the same as the website.
"""
import argparse, datetime, difflib, hashlib, json, pathlib, random, re, sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import free_chat_safety as fs
from measure_teacher import SCEN, facts_for
from make_conversations import flag_turns

ROOT = fs.ROOT
BY_SID = {v: k for k, v in SCEN.items()}


def words(t):
    """The reply without labels, stage directions or case: used to find repeats."""
    t = re.sub(r"\([^)]*\)", " ", t)
    t = re.sub(r"^\s*[*_]*[A-Z][a-z]+[*_]*\s*:", " ", t, flags=re.M)
    return " ".join(re.sub(r"[^\w' ]", " ", t.lower()).split())


def normalise(text, speakers, patient):
    """One line per speaker turn: 'Name: (direction) words'. Unlabelled text belongs to the previous speaker."""
    turns = []
    for para in re.split(r"\n\s*\n|\n", text.replace("*", "").strip()):
        para = para.strip()
        if not para:
            continue
        m = re.match(rf"^({'|'.join(speakers)})\s*:\s*", para)
        who = m.group(1) if m else None
        body = para[m.end():] if m else para
        d = re.match(rf"^\(\s*({'|'.join(speakers)})\s+", body)        # "(Teresa looks away)" names the speaker
        if d:
            who = who or d.group(1)
            body = "(" + body[d.end():]
        body = re.sub(r"\(\s*([A-Z])", lambda x: "(" + x.group(1).lower(), body)
        if who is None:
            who = turns[-1][0] if turns else patient
        if turns and turns[-1][0] == who:
            turns[-1][1] = (turns[-1][1] + " " + body).strip()
        else:
            turns.append([who, body.strip()])
    return "\n".join(f"{w}: {b}" for w, b in turns if b)


def near_probe(line, probes):
    a = " ".join(re.sub(r"[^\w' ]", " ", line.lower()).split())
    for p in probes:
        b = " ".join(re.sub(r"[^\w' ]", " ", p.lower()).split())
        if b in a or difflib.SequenceMatcher(None, a, b).ratio() >= 0.8:
            return p
    return None


def main():
    ap = argparse.ArgumentParser(description="Build training examples from practice conversations.")
    ap.add_argument("folders", nargs="+")
    ap.add_argument("--max-repeats", type=int, default=3)
    ap.add_argument("--valid", type=float, default=0.1, help="share of conversations held back for validation")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()

    convs = []
    for f in a.folders:
        p = pathlib.Path(f) if pathlib.Path(f).is_absolute() else ROOT / f
        convs += [dict(json.loads(l), source=p.name) for l in (p / "conversations.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    sids = {c["scenario"] for c in convs}
    if len(sids) != 1:
        raise SystemExit(f"Give folders from one scenario at a time (found {sorted(sids)}).")
    sid = sids.pop()
    short = BY_SID[sid]
    card = yaml.safe_load((ROOT / "scenarios" / sid / "role_card.yaml").read_text(encoding="utf-8"))
    first = lambda n: str(n).split()[0]
    speakers = [first(w["name"]) for w in [card["persona"], card.get("companion"), *(card.get("others") or [])] if w]
    patient = speakers[0]
    system = fs.system_prompt(sid)
    facts = facts_for(sid)
    prompt_id = hashlib.sha256(system.encode()).hexdigest()[:10]
    spec_path = ROOT / "evaluation" / f"{short}_hard_probes.yaml"
    probes = []
    if spec_path.exists():
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        probes = [p["text"] for p in spec["probes"]] + list(spec.get("warm_up", []))

    rng = random.Random(a.seed)
    order = list(range(len(convs)))
    rng.shuffle(order)
    n_valid = max(1, round(len(convs) * a.valid)) if a.valid > 0 else 0
    valid_ids = set(order[:n_valid])

    seen, kept = {}, {"train": [], "valid": []}
    stats = {"possible": 0, "kept": 0, "failed check": 0, "after a failed reply": 0, "near an exam question": 0,
             "after an exam question": 0, "repeat cap": 0}
    by_type = {}
    for ci, c in enumerate(convs):
        split = "valid" if ci in valid_ids else "train"
        T = by_type.setdefault(c["type"], {"conversations": 0, "kept": 0, "possible": 0})
        T["conversations"] += 1
        msgs = [{"role": "system", "content": system},
                {"role": "assistant", "content": normalise(c["opening"], speakers, patient)}]
        stop = None
        for t, (ck, e) in zip(c["turns"], flag_turns(short, c["turns"], facts)):
            t["checker"], t["early"] = ck, e
            stats["possible"] += 1
            T["possible"] += 1
            if stop:
                stats[stop] += 1
                continue
            if not t.get("reply") or t.get("checker") or t.get("early"):
                stats["failed check"] += 1
                stop = "after a failed reply"
                continue
            if probes and near_probe(t["clinician"], probes):
                stats["near an exam question"] += 1
                stop = "after an exam question"
                continue
            reply = normalise(t["reply"], speakers, patient)
            msgs = msgs + [{"role": "user", "content": t["clinician"].strip()}]
            key = words(reply)
            if seen.get(key, 0) >= a.max_repeats:
                stats["repeat cap"] += 1
            else:
                seen[key] = seen.get(key, 0) + 1
                stats["kept"] += 1
                T["kept"] += 1
                kept[split].append({"messages": msgs + [{"role": "assistant", "content": reply}],
                                    "meta": {"scenario": sid, "source": c["source"], "conversation": c["n"], "turn": t["turn"],
                                             "trainee": c["type"], "teacher": c["model"], "prompt_id": prompt_id}})
            msgs = msgs + [{"role": "assistant", "content": reply}]

    out = ROOT / "runtime" / "transcripts" / "training_data" / f"{short}_{datetime.datetime.now():%Y%m%d_%H%M}"
    out.mkdir(parents=True, exist_ok=True)
    for split, rows in kept.items():
        (out / f"{split}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    report(out, sid, a, convs, n_valid, stats, by_type, kept, prompt_id)
    print(f"{stats['kept']} examples kept of {stats['possible']} ({len(kept['train'])} train, {len(kept['valid'])} valid)")
    print("Report:", (out / "report.md").relative_to(ROOT))


def report(out, sid, a, convs, n_valid, stats, by_type, kept, prompt_id):
    allrows = kept["train"] + kept["valid"]
    tgt = [r["messages"][-1]["content"] for r in allrows]
    cnt = {}
    for t in tgt:
        cnt[words(t)] = cnt.get(words(t), 0) + 1
    L = [f"# Training data: {sid}", f"Built {datetime.datetime.now():%Y-%m-%d %H:%M} from: {', '.join(sorted({c['source'] for c in convs}))}",
         f"Conversations: {len(convs)} ({len(convs) - n_valid} train, {n_valid} valid) · max repeats {a.max_repeats} · prompt id {prompt_id}", "",
         "## What happened to each patient reply", "", "| | Replies |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in stats.items()]
    L += ["", "## By trainee type", "", "| Trainee | Conversations | Replies | Kept |", "|---|---|---|---|"]
    L += [f"| {k} | {v['conversations']} | {v['possible']} | {v['kept']} |" for k, v in by_type.items()]
    L += ["", "## Most repeated kept replies (words only)", ""]
    L += [f"- {v} x {k[:90]}" for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])[:8]]
    n = sum(len(r["messages"][-1]["content"].split()) for r in allrows)
    L += ["", "## Size", "", f"- examples: {len(allrows)}; target words: {n}; average {n / max(1, len(allrows)):.0f} words per reply",
          f"- system prompt: {len(allrows[0]['messages'][0]['content']) if allrows else 0} characters, repeated in every example", "",
          "## Format check", "",
          f"- targets with a speaker label on every line: {sum(1 for t in tgt if all(re.match(r'^[A-Z][a-z]+: ', x) for x in t.splitlines()))} of {len(tgt)}",
          f"- targets with stage directions: {sum(1 for t in tgt if '(' in t)}", "",
          "## Three random examples (last two messages)", ""]
    for r in random.Random(0).sample(allrows, min(3, len(allrows))):
        L += [f"- {r['meta']['trainee']}, conversation {r['meta']['conversation']}, turn {r['meta']['turn']}",
              f"  - Clinician: {r['messages'][-2]['content'][:200]}", f"  - Target: {r['messages'][-1]['content'][:250]}"]
    L += ["", "## Notes for training", "",
          "- Each example starts with the system prompt and the patient's opening line (an assistant message),",
          "  exactly as the website sends them. Some chat templates (Gemma's included) expect the first turn",
          "  to be the user's; check the template before training and adapt it if needed.",
          "- Train only on the last assistant message of each example."]
    (out / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
