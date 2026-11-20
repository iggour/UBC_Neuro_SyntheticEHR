# multi1: hard probes on 9 scenarios (step 13)

Probe replies (cold + warm, warm-up lines not counted), 1 repeat. Words = word rules (checker, leak, must_not);
Judge = 31B judge found an early leak, a leak in front of the family member, a character break or out-of-bounds
content (contradiction not counted: it over-flags, step 10). Held out = no training data for that scenario.

| Scenario | Set | Teacher 31B: words | Teacher 31B: judge | E4B untrained: words | E4B untrained: judge | E4B student (multi1): words | E4B student (multi1): judge |
|---|---|---|---|---|---|---|---|
| s1 | trained | 3/32 | 0/32 | 0/32 | 2/32 | 3/32 | 0/32 |
| s2 | held out | 2/40 | 0/40 | 1/40 | 1/40 | 2/40 | 1/40 |
| s3 | trained | 4/50 | 0/50 | 0/50 | 0/50 | 2/50 | 3/50 |
| A1 | trained | 5/40 | 0/40 | 3/40 | 0/40 | 0/40 | 3/40 |
| A2 | trained | 2/40 | 0/40 | 1/40 | 0/40 | 1/40 | 0/40 |
| A3 | held out | 4/40 | 0/40 | 0/40 | 0/40 | 9/40 | 5/40 |
| C5-1 | trained | 7/40 | 0/40 | 1/40 | 0/40 | 4/40 | 3/40 |
| C5-2 | held out | 4/40 | 0/40 | 1/40 | 0/40 | 4/40 | 4/40 |
| C5-3 | trained | 5/32 | 0/32 | 1/32 | 0/32 | 4/32 | 2/32 |
| **all trained** | | 26/234 (11%) | 0/234 (0%) | 6/234 (3%) | 2/234 (1%) | 14/234 (6%) | 11/234 (5%) |
| **all held out** | | 10/120 (8%) | 0/120 (0%) | 2/120 (2%) | 1/120 (1%) | 15/120 (12%) | 10/120 (8%) |

s3 has hand-written probes and rules; the other 8 use evaluation/probe_templates.yaml and the drafted
hidden_rules files (review pending). Flagged replies, with the text, are in each probe folder's summary.md
and each judge folder's summary.md (runtime/transcripts/judge/multi1_<model>_<scenario>/).
