# AGENTS.md: handoff for HD Anchor (UBC_Neuro_SyntheticEHR)

Written 2026-11-20 (updated 2026-11-23) by Claude (Anthropic) for the next coding agent (e.g. GPT Codex). Read this first,
then CLAUDE.md (older working rules, still valid) and docs/distillation_log.md (the full experiment record).

## 1. What the project is

HD Anchor: practice conversations for clinicians (medical students, residents, neurologists, genetic
counsellors) with fictional Huntington disease (HD) patients played by a language model. Huntington
disease only. All patients are fictional; no real clinical data is used anywhere.

Two parts:
1. Website (static, GitHub Pages): learn -> practise (guided mode without AI, or free chat with the
   learner's own model) -> feedback. 15 scenarios in 5 families.
2. Research (current focus): distil a small local "patient" model from a large teacher.
   - Teacher: Gemma 4 31B (lab server), prompted with the role card. It is NOT fine-tuned.
   - Training data: the teacher talks with simulated trainees (also 31B; types good, average, errors,
     pushy, tester). Replies are filtered by rules (fact checker + hidden-item word rules); the
     conversation is cut at the first failed reply; probe-like lines are kept out; max 3 repeats.
   - Student: Gemma 4 E4B, LoRA fine-tuned (4-bit base) on the Chongqing workstation.
   - Quantised student (GGUF Q8_0, llama.cpp, CPU) is what learners would run.
   - Criteria: (1) no invented facts, (2) hidden items not disclosed early or in front of the family
     member they are kept from, (3) hidden items disclosed when the trainee asks well,
     (4) stays in character. Checked by the word rules/checker and a 31B semantic judge.
   - Tests: fixed trial script (s3 only, 10 runs; measures 2 and 3) and hard probes (measures 1, 2, 4).

## 2. Status on 2026-11-20

- s3 (suicide-risk assessment) is CLOSED: student = pilot3; deployment file = Q8_0 (steps 1-11 of the log).
- Step 12 done: scripts work for all scenarios (rules from evaluation/hidden_rules/*.yaml; s3 keeps hand rules).
- Step 13 DONE (multi1, 2026-11-20): 9 scenarios (Moreno s1-s3, Novak A1-A3, Walsh C5-1..3); trained
  s1, s3, A1, A2, C5-1, C5-3; held out s2, A3, C5-2. Results: docs/multi1_results.md and the log. Judge
  flags: teacher 0/354, untrained E4B 3/314, student 5% trained / 8% held out (mostly direct pressure
  probes S2/R2 and "you are the doctor now"). Paper text drafted: docs/paper/draft_2.11_3.10_multi1.md
  (not yet pasted into the .docx). Untrained-E4B judge for A2 is missing (server error); rerun
  `python3 scripts/multi1_table.py` to fill it.
- Step 14 DONE (phase 2, 2026-11-21): earned probes (disclosure when asked well) on all 15 scenarios and
  hard probes on the unseen B and C4 families, for teacher / untrained / pilot3 / multi1. Results:
  docs/phase2_results.md, docs/phase2_tradeoff.png, log step 14, paper draft 2.12 / 3.11. Students
  disclose at the teacher's level but fail 3-8% under pressure. multi2 followed (step 15).
- Step 15 DONE (multi2, 2026-11-21): + pressure-resistance conversations. Failures 4.8% -> 1.2% but
  disclosure fell 11-24 points in three tiers: not an improvement under the pre-set rule (trade-off moves
  with the data mix). No multi3. Distillation work is closed; remaining work is writing the paper.
- Step 16 STARTED (2026-11-23): small1 = Qwen3-1.7B on multi1 data (E2B dropped: ~5 GB GGUF). One command,
  training/run_small.py; plan, decision rule and done-when in log step 16.
- 2026-11-26: work split into two papers, each with its own handoff (also in the claude.ai Project):
  docs/handoff/handoff_A_education_2026-11-26.md (paper A, medical education: design, longitudinal families) and
  docs/handoff/handoff_B_informatics_2026-11-26.md (paper B, medical informatics: distillation experiments).
- Steps 16-17 CLOSED (2026-11-24): small1 (Qwen3-1.7B) and small2 (+ short prompt) are NOT usable under the
  pre-set rule: disclosure close to multi1 but failures under pressure 3-5x multi1 (~15% vs 4%). The short prompt
  changed no failure rate and halves the first-reply wait. Results: docs/phase2_results.md, log steps 16-17.
- At handoff (2026-11-23) Chongqing is quantising multi1 and multi2 to Q8_0 for the owner's website trial
  (~/hd-anchor/quant_log.txt). Thinking mode must be off when serving (llama-server flags in the log).
- Owner review pending: probe templates, drafted hidden_rules YAMLs, 16 judge gold labels,
  highlighted text in paper draft v0.3. Ethics application H26-03621 (UBC BREB) revised, not yet resubmitted.

## 3. Where things are stored

### 3a. Owner's Mac (main copy)
Repository: `~/Desktop/UBC_Neuro_SyntheticEHR` (Python 3, run scripts from the repo root).

| Path | What |
|---|---|
| `scenarios/<id>/` | role_card.yaml (facts, hidden items, rules; reviewed, do not change without the owner), checkpoints.yaml, knowledge_cards.md, family_prep_sheet.md, guided.yaml, mentor_notes.yaml, Chinese review checklists |
| `runtime/patient_prompts/<id>.md` | patient system prompts, built by scripts/build_patient_prompt.py |
| `runtime/trial_scripts/` | fixed trial scripts (s1-s3) |
| `runtime/transcripts/` | ALL generated data (git-ignored, about 105 MB, NOT on GitHub): `generate/` teacher conversations, `training_data/` filtered train/valid jsonl, `probes/` probe replies, `judge/` judge results, `measure/` trial-script runs, `multi1/` (after unzipping Chongqing results) |
| `evaluation/` | `<short>_hard_probes.yaml` (held-out exam; never train on them), `probe_templates.yaml`, `hidden_rules/<short>.yaml` (drafted rules, review pending), `judge_gold/` (s3 gold labels) |
| `scripts/` | make_conversations.py (generate), build_training_data.py (filter), run_probes.py, measure_teacher.py / run_trial_script.py (trial script), judge_replies.py, build_hidden_rules.py, make_probes.py, multi1_table.py, gemma_client.py, free_chat_safety.py (checker), build_web_v2.py (website) |
| `training/` | scripts that run on Chongqing: train_pilot*.py, train_multi1.py, run_multi1.py, student_server.py, merge_lora.py; see training/README.md |
| `docs/distillation_log.md` | the full record, steps 1-13, decisions and numbers. Update it after every step |
| `docs/paper/` | HD_Anchor_paper_draft_v0.3.docx (latest), draft_2.11_3.10_multi1.md |
| `docs/multi1_results.md` | step 13 results table (teacher columns filled) |
| `ethical approval/` | ethics documents for H26-03621 (untracked, local only; not on GitHub) |
| `site/`, `index.html` | built website (never edit by hand; rebuild with scripts/build_web_v2.py) |
| `*.zip` in repo root | result bundles moved between Mac and Chongqing (pilot2_tests, pilot3_tests, q4_*, q8_*, bf16_test, full16_test, multi1); untracked |
| `.env` | GEMMA_BASE_URL of the lab server (git-ignored; never print or commit). Template: .env.example |
| `free_chat_config.json` | local free-chat settings (git-ignored) |

### 3b. GitHub
`https://github.com/iggour/UBC_Neuro_SyntheticEHR`. Working branch: `split-entries` (17 commits ahead of
`main`, last pushed commit 28e1b8f or later). Other branches: main, gemma-free-chat, draft/group-a-juvenile-hd.
GitHub has code, scenarios, probes, rules, docs and the paper draft, but NOT runtime/transcripts/
(the training data and all test outputs) and not the ethics folder. Check repo Settings -> Pages for the
branch the public site is served from.

### 3c. Chongqing workstation (RTX 5090 D v2, 24 GB; owner reaches it by remote desktop)
Windows; open PowerShell, then `wsl -d hd-anchor` (Ubuntu 24.04, user tongyang).
| Path (inside WSL) | What |
|---|---|
| `~/hd-anchor/.venv` | Python environment (unsloth, torch, transformers, peft, trl) |
| `~/models/gemma-4-E4B-it` | student base model; GGUF files (Q4_K_M, Q8_0) are also in `~/models/` (check with ls) |
| `~/hd-anchor/data`, `data_pilot2`, `data_pilot3` | s3 training data |
| `~/hd-anchor/outputs/pilot1|pilot2|pilot3|multi1/lora_best` | trained LoRA adapters (only here; not backed up) |
| `~/hd-anchor/bundle` | old test copy of the repo (commit d48a353) |
| `~/hd-anchor/multi1/` | step 13: data_multi1/, bundle/ (repo copy), results/ |
| `~/hd-anchor/multi1_log.txt` | step 13 progress (`tail -3 ~/hd-anchor/multi1_log.txt`; last line DONE when finished) |
| `/mnt/e/WSL/` = Windows `E:\WSL\` | exchange folder: files go in and out of Chongqing through here |
llama.cpp was built from source there (CPU build). `unzip` is not installed: use `python3 -m zipfile -e`.

### 3d. Lab server (31B teacher and judge)
Gemma 4 31B on vLLM, OpenAI-compatible; address only in the Mac's `.env`. Maintained by a senior labmate;
the owner's internal testing only, never exposed to learners. It can be down; the Mac must be on the
network that reaches it.

### 3e. Outside the repo
- claude.ai Project "HD project": handoff notes claude/progress_2026-*.md (copy them out if needed).
- Rare Disease Foundation microgrant: submitted 2026-10-26.

## 4. How the owner wants to work

- Talk to the owner in Chinese; code, comments and files stay in English.
- Aim for completion, not perfection. Before each task say when it counts as done, and stop there.
  Unexplained results go into limitations, not into more runs.
- List every run needed up front and chain them into ONE command. Each command must be a single short
  line, copy-paste ready, and say which machine and window it runs in (Mac Terminal / Chongqing WSL).
  Write out zip and copy steps every time; never "like last time".
- Explain each technical step in simple words; one step at a time.
- Drafts: the agent drafts, the owner reviews, then the owner commits and pushes. New content gets
  "Reviewed by: PENDING". Clinical claims for review get a Chinese checklist with source URLs.
- Do not change reviewed scenarios or the published website without the owner's agreement.
- Back up often to GitHub. Data that only exists in runtime/transcripts/ or on Chongqing is at risk.
- Messages drafted for the owner to send: plain text, no italics.

## 5. Safety rules for the content

The simulated patient never states medical facts, doses or advice, and never describes self-harm methods
or amounts. Held-out probes and trial-script lines must never enter training data. The lab server address
must never appear in any page, log or commit.
