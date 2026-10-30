# CLAUDE.md: HD Anchor (UBC_Neuro_SyntheticEHR)

Read this first in every session. Last updated 2026-10-29.

## What this project is
HD Anchor: clinicians practise three hard conversations in Huntington disease (HD) care with
fact-anchored simulated patients. Huntington disease only; no other diseases for now.
A Rare Disease Foundation microgrant was submitted on 2026-10-26.

- Users: medical students, residents, neurologists, genetic counsellors.
- Flow: Learn (knowledge cards) -> Practise (simulated patient + mentor hints, can be switched off)
  -> Feedback (checkpoint list linked to sources).
- Three scenarios, one fictional family (Moreno):
  - s1_pretest_counselling: Leah, 28, wants predictive testing "today".
  - s2_disclosing_result: Leah + fiance Marco, positive result (HTT CAG 19/43).
  - s3_suicide_risk_assessment: Teresa (Leah's mother, 54, early HD, on tetrabenazine) + husband Luis.
- Phase 1 has NO human participants (no ethics approval yet). Testing uses simulated trainees only.

## Rules for working in this repo (the owner's preferences)
1. Content workflow: Claude drafts -> the owner reviews -> saved locally -> owner pushes to GitHub.
   Never commit or push unless asked.
2. Anything clinical that needs checking gets a Chinese review checklist (审核清单_*_中文.md) with
   the source URL for each claim. Mark new files "Reviewed by: PENDING" until the owner approves.
3. Do not change reviewed scenario content (scenarios/*) or the published website without the
   owner's agreement. Format-only fixes are fine; say what you changed.
4. Facts in role cards are canonical. Ages, names, CAG numbers and timelines must match across
   s1-s3. The patient never states medical facts, ranges, doses or advice. The patient never
   describes self-harm methods or amounts.
5. Mentor hints and feedback are pre-written and sourced (checkpoints.yaml). An AI may judge
   met / not met, but never writes its own clinical advice.
6. Messages drafted for the owner to send: plain text, no italics.
7. The owner prefers to discuss in Chinese; code, comments and file content stay in English.

## Repository map
- scenarios/<id>/role_card.yaml       Patient facts, hidden concerns, behaviour rules (reviewed)
- scenarios/<id>/checkpoints.yaml     Mentor checkpoints C1-C9, red flags, sources (reviewed)
- scenarios/<id>/knowledge_cards.md   Learn-step cards with [sN] source tags (reviewed)
- scenarios/<id>/family_prep_sheet.md Family appointment sheet + question builder (reviewed)
- scenarios/<id>/guided.yaml          Guided mode: pre-written branching turns (PENDING review)
- scenarios/<id>/审核清单_*_中文.md     Chinese review checklists
- scripts/build_web_v2.py + scripts/web_v2_template.html -> web/hd_anchor_v2.html
  The website is generated from scenarios/. Edit the scenario or the template, then rebuild.
  Never hand-edit web/hd_anchor_v2.html. web/hd_training_prototype.html is the old version.
- records/                            Synthetic patient records for Cases 3-4 (Record tab, PENDING review)
- scripts/build_patient_prompt.py     role_card.yaml -> runtime/patient_prompts/<id>.md
- scripts/gemma_client.py             OpenAI-compatible client (stdlib only)
- scripts/patient_session.py, chat_patient.py, run_trial_script.py
                                      Talk to the AI patient / run the trial scripts
- runtime/trial_scripts/              Bilingual trial scripts (rounds A good, B poor, C stress)
- runtime/transcripts/                Test transcripts (git-ignored)
- prompts/, demos/, older scripts     Earlier synthetic-EHR work (3-layer prompts, checker v0)

After changing a role card: run build_patient_prompt.py. After changing any scenario file or the
template: run build_web_v2.py, then open the page and click through all three scenarios.

## Model access
- Gemma 4 31B (gemma-4-31B-it) on vLLM, OpenAI-compatible, base URL in .env (GEMMA_BASE_URL).
  No API key is needed at the moment. Context length 262144.
- .env is git-ignored. Never print, log or commit the URL or any key. .env.example is the template.
- Cloudflare blocks Python's default User-Agent (403); gemma_client.py sends its own.
- The GPU is shared by the lab: run large batches off-peak and keep request rates modest.
- Quick test: python3 scripts/gemma_client.py

## Current status (2026-10-29)
- Done: 3 reviewed scenarios; website v2 with Learn / Practise (guided mode for s1-s3) / Feedback,
  family zone, sources; bilingual trial scripts; Gemma test scripts.
- Pending owner review: guided.yaml for s1-s3 (checklists 审核清单_引导模式_中文.md).
- Not yet pushed: guided mode, bilingual trial scripts, Gemma scripts (see git status).

## Next steps
1. Run run_trial_script.py for s3, s2, s1 against Gemma 4 31B. Score each transcript on five checks
   (keeps secrets, no made-up facts, stays in character, reacts to the clinician, safe) using the
   table in runtime/trial_scripts/README_试玩说明.md. Note which prompt rules fail.
2. If the patient is unreliable, add a compact patient prompt variant and compare.
3. Offline generation pipeline (main line): see docs/offline_generation_workflow.md.
4. Later, internal only: free-conversation mode with a hybrid AI mentor (yes/no checkpoint judging)
   and automated testing with simulated trainees.
