# Handoff: Paper A (medical education), 2026-11-26

Start a new chat with: "继续 A 篇，先读项目里的 handoff_A_education_2026-11-26.md 和仓库的 AGENTS.md". Reply in Chinese.
(Copy of the claude.ai Project doc claude/handoff_A_education_2026-11-26.md, kept in the repo as a backup.)

## What paper A is
Design and technical evaluation of HD Anchor as a teaching platform. Value (owner's words): the design architecture, longitudinal families, the possible downloadable small model running on learners' computers, and possible report-writing teaching. Distillation details belong to paper B (medical informatics); A only cites B's conclusions.

## Decisions already made (owner, 2026-11-26)
- Title: "HD Anchor: design and technical evaluation of a longitudinal, fact-anchored simulation platform for difficult conversations in Huntington disease" (option A).
- Longitudinal design wording: the owner described it as "one person at three time points". More exact: one FAMILY followed at three time points; the person with HD is the thread, but the person in the room changes in every family (e.g. Moreno: Leah s1-s2, her mother Teresa s3; Novak: Sarah (mother) A1, Maya A2, Sarah about son Owen A3; Fraser: Ruth B1-B2, husband George B3; Brennan: Mark C4-1/C4-2, wife Anna C4-3; Walsh: Kevin in all three). Established education term: "unfolding case" (a case that evolves over time, new situations revealed at each encounter; NLN ACE.S unfolding cases are family-based and framed as continuity of care) -> use "longitudinal, family-based unfolding cases". Literature on unfolding cases is mainly nursing education (e.g. scoping review, J Adv Med Educ Prof 2026, PMC12858445).
- Report teaching (annotated MRI reports): written as "planned" in the paper; the feature itself can be started now (needs the owner's agreement before any website change). Case 3 (Fraser) and Case 4 (Brennan) already have reports in records/case3_fraser.yaml, records/case4_brennan.yaml (kinds: mri, genetic, swallowing).
- Reviewers and authors: add later.
- Submission: AFTER ethics approval (H26-03621) and after the expert content review is done (paper should include expert review data). Journal: decide at submission time.
- Pre-set decision rules: one sentence in methods only.

## Files
- Chinese discussion draft: docs/paper/A篇_医学教育_中文讨论稿_v0.1.docx (built in the cloud by a docx-js script; yellow = key points; red 【待决定】 = owner questions). Next version should apply the decisions above (title, "unfolding case" wording + the family/person table, report teaching as planned, Q6 answered).
- Earlier combined draft (now split): docs/paper/HD_Anchor_论文中文讨论稿_v0.4.docx. English draft v0.3 (s3-focused): docs/paper/HD_Anchor_paper_draft_v0.3.docx; draft text for multi-scenario sections: docs/paper/draft_2.11_3.10_multi1.md.
- New analyses for A (no model calls): scripts/paperA_checks.py -> docs/paperA_checks.md. Website checker catches 5 of multi1's 28 hard-probe failures (residual 3.9%); blocks 0-2 earned disclosures; withholds 10.8% of the teacher's acceptable replies (in-character echoes of "simulation", "role card"); adding hidden-item word rules would cut multi1's residual to 1.4% but block 89 of 122 earned disclosures. Judge contradictions: teacher 0.3%, E4B students 2.7-3.8%, 1.7B 10.6-11.4%, mostly probe F2 ("your last brain scan was completely normal").
- Website: built by scripts/build_web_v2.py into site/ (never edit by hand; no website change without the owner's agreement). Scenarios: scenarios/<id>/ (role_card.yaml, checkpoints.yaml, knowledge_cards.md, family_prep_sheet.md, guided.yaml, mentor_notes.yaml). Consistency: python3 scripts/check_role_cards.py (all 15 pass, checked 2026-11-26). Timeline per scenario: scenario.months_after_* in role_card.yaml.
- Ethics status: project doc claude/ethics_H26-03621_status.md (round-2 provisos pending; study uses guided mode only).

## Open tasks for A (suggested order)
1. Apply the decisions to the Chinese draft (v0.2) and show the owner.
2. Literature: unfolding cases / longitudinal simulated patients / continuity-of-care simulation; LLM simulated patients; HD education resources (Huntington Academy). Owner wants Chinese summaries with URLs to check.
3. Figures: website screenshots, Learn-Practise-Feedback flow, family timeline figure.
4. Report teaching feature: design note first (annotation layer on existing MRI reports: evidence + knowledge point per sentence, standard structure, exercises such as writing the impression or spotting errors); clinical content needs a Chinese review checklist with source URLs; owner approves before building.
5. Optional: compare the in-page JS checker with free_chat_safety.check_reply line by line (minutes).
6. Owner items: judge gold check (14), hidden_rules review, ethics resubmission.

## Working style
Reply in Chinese; code/commands stay as they are. State when a task counts as done before starting; no endless iteration. Claude drafts, owner reviews, owner commits and pushes. Paper drafts for discussion in Chinese with yellow highlights, as .docx. Plain text (no italics) for messages the owner sends.
