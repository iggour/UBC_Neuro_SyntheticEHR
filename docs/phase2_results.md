# Phase 2: keeping secrets and opening up (15 scenarios, 4 models)

Hard-probe failures (lower is better): replies the 31B judge found to leak a hidden item early, leak it in
front of the family member, break character or go out of bounds (1 repeat). Disclosure (higher is better):
earned probes (rapport, family member asked out if needed, one good question; 2 repeats) whose target item
the judge found in the reply. Tiers are defined by multi1's training data; pilot3 was trained on s3 only.

## By tier

| Model | s3: failures | s3: disclosure | trained (multi1): failures | trained (multi1): disclosure | held out, same family: failures | held out, same family: disclosure | unseen family: failures | unseen family: disclosure |
|---|---|---|---|---|---|---|---|---|
| Teacher 31B | 0/50 (0%) | - | 0/184 (0%) | - | 0/120 (0%) | - | - | - |
| E4B untrained | 0/50 (0%) | - | 2/184 (1%) | - | 1/120 (1%) | - | - | - |
| pilot3 (s3 only) | - | - | - | - | - | - | - | - |
| multi1 (6 scenarios) | 3/50 (6%) | - | 8/184 (4%) | - | 10/120 (8%) | - | - | - |

## By scenario

| Scenario | Tier | Teacher 31B: fail | Teacher 31B: discl | E4B untrained: fail | E4B untrained: discl | pilot3 (s3 only): fail | pilot3 (s3 only): discl | multi1 (6 scenarios): fail | multi1 (6 scenarios): discl |
|---|---|---|---|---|---|---|---|---|---|
| s1 | trained (multi1) | 0/32 | - | 2/32 | - | - | - | 0/32 | - |
| s2 | held out, same family | 0/40 | - | 1/40 | - | - | - | 1/40 | - |
| s3 | s3 | 0/50 | - | 0/50 | - | - | - | 3/50 | - |
| A1 | trained (multi1) | 0/40 | - | 0/40 | - | - | - | 3/40 | - |
| A2 | trained (multi1) | 0/40 | - | 0/40 | - | - | - | 0/40 | - |
| A3 | held out, same family | 0/40 | - | 0/40 | - | - | - | 5/40 | - |
| C5-1 | trained (multi1) | 0/40 | - | 0/40 | - | - | - | 3/40 | - |
| C5-2 | held out, same family | 0/40 | - | 0/40 | - | - | - | 4/40 | - |
| C5-3 | trained (multi1) | 0/32 | - | 0/32 | - | - | - | 2/32 | - |
| B1 | unseen family | - | - | - | - | - | - | - | - |
| B2 | unseen family | - | - | - | - | - | - | - | - |
| B3 | unseen family | - | - | - | - | - | - | - | - |
| C4-1 | unseen family | - | - | - | - | - | - | - | - |
| C4-2 | unseen family | - | - | - | - | - | - | - | - |
| C4-3 | unseen family | - | - | - | - | - | - | - | - |

Earned-probe questions were drafted automatically (hidden_rules tests); some are short and assume
context, so even the teacher does not disclose every item. Compare models with each other, not with 100%.
