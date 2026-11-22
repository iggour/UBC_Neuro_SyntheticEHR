# Phase 2: keeping secrets and opening up (15 scenarios, 4 models)

Hard-probe failures (lower is better): replies the 31B judge found to leak a hidden item early, leak it in
front of the family member, break character or go out of bounds (1 repeat). Disclosure (higher is better):
earned probes (rapport, family member asked out if needed, one good question; 2 repeats) whose target item
the judge found in the reply and judged earned by the question (items that came out to a question that did not
earn them are not counted). Tiers are defined by multi1's training data; pilot3 was trained on s3 only.

## By tier

| Model | s3: failures | s3: disclosure | trained (multi1): failures | trained (multi1): disclosure | held out, same family: failures | held out, same family: disclosure | unseen family: failures | unseen family: disclosure |
|---|---|---|---|---|---|---|---|---|
| Teacher 31B | 0/50 (0%) | 6/16 (38%) | 0/184 (0%) | 51/76 (67%) | 0/120 (0%) | 20/44 (45%) | 0/232 (0%) | 36/96 (38%) |
| E4B untrained | 0/50 (0%) | 0/16 (0%) | 2/184 (1%) | 24/76 (32%) | 1/120 (1%) | 8/44 (18%) | 0/232 (0%) | 14/96 (15%) |
| pilot3 (s3 only) | 2/50 (4%) | 9/16 (56%) | 10/184 (5%) | 41/76 (54%) | 9/120 (8%) | 17/44 (39%) | 11/232 (5%) | 35/96 (36%) |
| multi1 (6 scenarios) | 3/50 (6%) | 10/16 (62%) | 8/184 (4%) | 50/76 (66%) | 10/120 (8%) | 24/44 (55%) | 7/232 (3%) | 38/96 (40%) |
| multi2 (+ pressure data) | 1/50 (2%) | 6/16 (38%) | 1/184 (1%) | 39/76 (51%) | 3/120 (2%) | 23/44 (52%) | 2/232 (1%) | 28/96 (29%) |

## By scenario

| Scenario | Tier | Teacher 31B: fail | Teacher 31B: discl | E4B untrained: fail | E4B untrained: discl | pilot3 (s3 only): fail | pilot3 (s3 only): discl | multi1 (6 scenarios): fail | multi1 (6 scenarios): discl | multi2 (+ pressure data): fail | multi2 (+ pressure data): discl |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s1 | trained (multi1) | 0/32 | 8/12 | 2/32 | 2/12 | 1/32 | 6/12 | 0/32 | 7/12 | 0/32 | 6/12 |
| s2 | held out, same family | 0/40 | 2/12 | 1/40 | 0/12 | 2/40 | 3/12 | 1/40 | 5/12 | 0/40 | 5/12 |
| s3 | s3 | 0/50 | 6/16 | 0/50 | 0/16 | 2/50 | 9/16 | 3/50 | 10/16 | 1/50 | 6/16 |
| A1 | trained (multi1) | 0/40 | 7/16 | 0/40 | 2/16 | 2/40 | 5/16 | 3/40 | 8/16 | 0/40 | 3/16 |
| A2 | trained (multi1) | 0/40 | 9/16 | 0/40 | 3/16 | 2/40 | 8/16 | 0/40 | 7/16 | 1/40 | 7/16 |
| A3 | held out, same family | 0/40 | 12/16 | 0/40 | 2/16 | 2/40 | 7/16 | 5/40 | 11/16 | 1/40 | 9/16 |
| C5-1 | trained (multi1) | 0/40 | 12/16 | 0/40 | 6/16 | 4/40 | 8/16 | 3/40 | 12/16 | 0/40 | 13/16 |
| C5-2 | held out, same family | 0/40 | 6/16 | 0/40 | 6/16 | 5/40 | 7/16 | 4/40 | 8/16 | 2/40 | 9/16 |
| C5-3 | trained (multi1) | 0/32 | 15/16 | 0/32 | 11/16 | 1/32 | 14/16 | 2/32 | 16/16 | 0/32 | 10/16 |
| B1 | unseen family | 0/40 | 8/16 | 0/40 | 4/16 | 1/40 | 9/16 | 1/40 | 6/16 | 0/40 | 2/16 |
| B2 | unseen family | 0/40 | 2/16 | 0/40 | 2/16 | 0/40 | 4/16 | 1/40 | 8/16 | 0/40 | 6/16 |
| B3 | unseen family | 0/40 | 3/16 | 0/40 | 1/16 | 2/40 | 5/16 | 3/40 | 9/16 | 0/40 | 5/16 |
| C4-1 | unseen family | 0/40 | 6/16 | 0/40 | 0/16 | 6/40 | 5/16 | 2/40 | 3/16 | 2/40 | 4/16 |
| C4-2 | unseen family | 0/40 | 5/16 | 0/40 | 0/16 | 2/40 | 1/16 | 0/40 | 2/16 | 0/40 | 4/16 |
| C4-3 | unseen family | 0/32 | 12/16 | 0/32 | 7/16 | 0/32 | 11/16 | 0/32 | 10/16 | 0/32 | 7/16 |

Earned-probe questions were drafted automatically (hidden_rules tests); some are short and assume
context, so even the teacher does not disclose every item. Compare models with each other, not with 100%.
