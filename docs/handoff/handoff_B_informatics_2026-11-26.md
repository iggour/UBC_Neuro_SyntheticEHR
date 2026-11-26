# Handoff: Paper B (medical informatics), 2026-11-26

Start a new chat with: "继续 B 篇，先读项目里的 handoff_B_informatics_2026-11-26.md、仓库的 AGENTS.md 和 docs/distillation_log.md". Reply in Chinese.
(Copy of the claude.ai Project doc claude/handoff_B_informatics_2026-11-26.md, kept in the repo as a backup.)

## What paper B is
Distilling a fact-anchored LLM simulated patient (Huntington disease) into small local models, with a two-sided evaluation: keeping secrets (hard probes) AND opening up when the trainee asks well (earned probes). Owner's view: the current findings alone are close to "expected results"; B needs stronger experiments: training methods and more evaluation dimensions are the next focus.

## Where the experiments stand (steps 1-17, all CLOSED; details in docs/distillation_log.md)
- Teacher Gemma 4 31B (lab server, not fine-tuned). Students: pilot1-3 (s3 only), multi1 (6 scenarios), multi2 (+ pressure data) on Gemma 4 E4B (4-bit base + LoRA r16); small1, small2 on Qwen3-1.7B (16-bit base + LoRA; small2 = short prompt without the guideline layer, context distillation).
- 15 scenarios, tiers: s3 / trained (s1, A1, A2, C5-1, C5-3) / held out same family (s2, A3, C5-2) / unseen families (B1-B3, C4-1..3). Per model: 586 hard-probe replies (1 repeat), 232 earned-probe replies (2 repeats). Judge = 31B, validated on 193 s3 gold labels and 95/100 on other scenarios.
- Failures / disclosure by tier (s3, trained, held out, unseen): teacher 0/38, 0/67, 0/45, 0/38; untrained E4B 0/0, 1/32, 1/18, 0/15; multi1 6/62, 4/66, 8/55, 3/40; multi2 2/38, 1/51, 2/52, 1/29; small1 8/38, 15/68, 21/39, 16/37; small2 12/31, 14/53, 17/55, 15/38 (%).
- Key statistics (cluster bootstrap over scenarios, docs/phase2_stats.md): multi1 vs teacher disclosure +3.9 (p=0.46), failures +4.8 (p<0.001); multi2 vs multi1 failures -3.6 (p<0.001), disclosure -11.2 (p=0.006); small1 vs multi1 failures +11.3 (p<0.001), disclosure -5.2 (p=0.27); small2 vs small1 failures -1.2 (p=0.61).
- Main readings: (1) trained students reach the teacher's disclosure and transfer to unseen families; (2) the secrecy/openness balance follows the data mix; (3) shrinking is asymmetric: 1.7B keeps opening up but secrecy collapses (early leaks, character breaks on role/system manipulation probes J2, J3, R2); (4) the unused guideline layer can be dropped at no measurable safety cost (prompt 4,005 -> 1,837 tokens; first CPU reply 15.8 -> 7.8 s).
- Extra analyses (docs/paperA_checks.md): website checker catches few leaks; hidden-item word rules would block 73% of legitimate disclosures; judge contradictions teacher 0.3%, E4B students ~3%, 1.7B ~11% (mostly false-premise probe F2).
- Deployment: GGUF Q8_0 multi1 7.5 GB; small Q8_0 2.17 GB / Q4_K_M 1.28 GB. Quantised files NOT probe-tested. Qwen3 students write an empty <think></think> first (serve with --reasoning-format deepseek, without enable_thinking=false; untested).

## Gaps a reviewer would raise (candidate experiments; owner chooses)
1. Seeds: one training seed per model. 1.7B is cheap (~35 min training + ~15 min GPU tests on Chongqing; judge ~1.5-1.7 h per model on the Mac).
2. Second judge from another model family (e.g. a ~30B open model on Chongqing via ModelScope), or more human labels.
3. Baselines: untrained Qwen3-1.7B; prompt-only small model.
4. A method that improves the trade-off: preference training (DPO) with paired kept/leaked replies; contrast pairs (same item, bad question -> withhold, good question -> disclose); conditional injection of hidden items into the prompt only when the condition is met (structural); more epochs (small1/small2 still improving at the last step).
5. More evaluation dimensions: contradiction (judge already returns it), responsiveness to empathy (same question asked warmly vs bluntly), longitudinal consistency of family facts across a family's three scenarios, reply length/naturalness.
6. Repeats (hard 1, earned 2) and probe tests of the quantised files.
Before any run: state the done-when, list all runs, chain them into one command, set the decision rule.

## Machines and how runs work
- Mac (owner): repo ~/Desktop/UBC_Neuro_SyntheticEHR; the ONLY machine that reaches the lab server (judge, teacher). Check with python3 scripts/check_server.py (prints status, never the address; .env must never be printed or committed). Claude's device shell cannot reach the server. Judge: python3 scripts/phase2_table.py && python3 scripts/phase2_stats.py (adds rows automatically for models listed in phase2_table.MODELS). Keep the Mac awake: caffeinate -i -w $(pgrep -f phase2_table.py | head -1).
- Chongqing (RTX 5090 D v2, 24 GB): PowerShell -> wsl -d hd-anchor (prompt tongyang@...$). Hugging Face and hf-mirror are blocked; models come from ModelScope (Qwen3-1.7B at ~/models/Qwen3-1.7B). venv ~/hd-anchor/.venv; data ~/hd-anchor/multi1/data_multi1; llama.cpp CPU build ~/llama.cpp/build/bin. LoRAs only there: outputs/pilot1-3, multi1, multi2, small1 (also E:\WSL\small1_lora.zip), small2. The GPU check in the run scripts cannot see Windows-side GPU jobs (another project, BBDM_SAM_5090, sometimes runs there).
- Pattern (steps 16-17): Claude builds a bundle zip on the Mac (git archive + changed files, no .env), owner sends it by WeChat; on Chongqing WeChat web saves to C:\Users\admin\Downloads, so commands should look in /mnt/e/WSL/ and /mnt/c/Users/admin/Downloads/. One unattended script (training/run_small.py NAME [short]) trains, tests, merges, quantises, measures CPU speed and zips results to E:\WSL\NAME_results.zip with paths relative to the results folder. Owner sends results back; phase2_table.py unzips them.
- Analysis code: phase2_table.py / phase2_stats.py (models, tiers, bootstrap), paperA_checks.py (checker, contradictions), judge_replies.py.

## Paper status
Combined Chinese draft (before the A/B split): docs/paper/HD_Anchor_论文中文讨论稿_v0.4.docx (storyline: two-sided evaluation -> transfer -> trade-off -> size limit). The owner finds "untrained models look safe by saying nothing" too obvious as a finding: use it as motivation, lead with transfer, trade-off and the asymmetric collapse. Next: a B-specific Chinese discussion draft after the owner picks the experiments.

## Working style
Reply in Chinese; code/commands stay as they are. Before each task say when it counts as done; no endless iteration; unexplained results go to limitations. List every run up front; one short single-line copy-paste command per machine, saying which machine/window. Explain technical steps simply, one step at a time. Owner commits and pushes. Paper drafts for discussion: Chinese .docx with yellow highlights.
