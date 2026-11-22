# Phase 2 statistics

Made by scripts/phase2_stats.py from the judged files behind docs/phase2_results.md.
Rates with Wilson 95% confidence intervals. Differences: cluster bootstrap over scenarios (10,000 draws),
95% percentile interval and two-sided p. Failures: hard probes (lower is better). Disclosure: earned probes
(higher is better). Replies within a scenario are correlated, so tests resample whole scenarios.

## 1. Rates by tier

### Hard-probe failures

| Model | s3 | trained (multi1) | held out, same family | unseen family |
|---|---|---|---|---|
| Teacher 31B | 0% (0-7) 0/50 | 0% (0-2) 0/184 | 0% (0-3) 0/120 | 0% (0-2) 0/232 |
| E4B untrained | 0% (0-7) 0/50 | 1% (0-4) 2/184 | 1% (0-5) 1/120 | 0% (0-2) 0/232 |
| pilot3 (s3 only) | 4% (1-13) 2/50 | 5% (3-10) 10/184 | 8% (4-14) 9/120 | 5% (3-8) 11/232 |
| multi1 (6 scenarios) | 6% (2-16) 3/50 | 4% (2-8) 8/184 | 8% (5-15) 10/120 | 3% (1-6) 7/232 |
| multi2 (+ pressure data) | 2% (0-10) 1/50 | 1% (0-3) 1/184 | 2% (1-7) 3/120 | 1% (0-3) 2/232 |

### Disclosure when earned

| Model | s3 | trained (multi1) | held out, same family | unseen family |
|---|---|---|---|---|
| Teacher 31B | 38% (18-61) 6/16 | 67% (56-77) 51/76 | 45% (32-60) 20/44 | 38% (28-47) 36/96 |
| E4B untrained | 0% (0-19) 0/16 | 32% (22-43) 24/76 | 18% (10-32) 8/44 | 15% (9-23) 14/96 |
| pilot3 (s3 only) | 56% (33-77) 9/16 | 54% (43-65) 41/76 | 39% (26-53) 17/44 | 36% (28-46) 35/96 |
| multi1 (6 scenarios) | 62% (39-82) 10/16 | 66% (55-75) 50/76 | 55% (40-68) 24/44 | 40% (30-50) 38/96 |
| multi2 (+ pressure data) | 38% (18-61) 6/16 | 51% (40-62) 39/76 | 52% (38-66) 23/44 | 29% (21-39) 28/96 |

## 2. Differences between models (second minus first, percentage points)

### Hard-probe failures

| Comparison | all 15 scenarios | seen by multi1 (6) | new to multi1 (9) |
|---|---|---|---|
| multi1 (6 scenarios) vs pilot3 (s3 only) | -0.7 (-2.9 to +1.4), p=0.592 | -0.4 (-3.0 to +1.8), p=0.876 | -0.9 (-4.0 to +2.3), p=0.677 |
| multi2 (+ pressure data) vs multi1 (6 scenarios) | -3.6 (-5.4 to -1.8), p<0.001 | -3.8 (-6.6 to -0.8), p=0.027 | -3.4 (-5.7 to -1.4), p<0.001 |
| multi1 (6 scenarios) vs Teacher 31B | +4.8 (+2.9 to +6.7), p<0.001 | +4.7 (+2.1 to +7.0), p=0.002 | +4.8 (+2.3 to +7.7), p<0.001 |
| multi2 (+ pressure data) vs Teacher 31B | +1.2 (+0.3 to +2.2), p=0.005 | +0.9 (+0.0 to +1.7), p=0.182 | +1.4 (+0.0 to +2.8), p=0.055 |
| multi1 (6 scenarios) vs E4B untrained | +4.3 (+1.9 to +6.5), p<0.001 | +3.8 (-0.4 to +7.0), p=0.086 | +4.5 (+1.8 to +7.5), p<0.001 |
| pilot3 (s3 only) vs E4B untrained | +4.9 (+2.8 to +7.2), p<0.001 | +4.3 (+1.2 to +7.0), p=0.013 | +5.4 (+2.4 to +8.8), p<0.001 |

### Disclosure when earned

| Comparison | all 15 scenarios | seen by multi1 (6) | new to multi1 (9) |
|---|---|---|---|
| multi1 (6 scenarios) vs pilot3 (s3 only) | +8.6 (+1.3 to +15.8), p=0.028 | +10.9 (+2.3 to +18.7), p=0.013 | +7.1 (-3.7 to +17.4), p=0.231 |
| multi2 (+ pressure data) vs multi1 (6 scenarios) | -11.2 (-19.0 to -3.1), p=0.007 | -16.3 (-29.3 to -3.1), p=0.020 | -7.9 (-16.7 to +0.8), p=0.102 |
| multi1 (6 scenarios) vs Teacher 31B | +3.9 (-5.4 to +14.0), p=0.473 | +3.3 (-6.0 to +13.0), p=0.629 | +4.3 (-9.3 to +19.3), p=0.606 |
| multi2 (+ pressure data) vs Teacher 31B | -7.3 (-17.4 to +2.7), p=0.178 | -13.0 (-23.9 to -2.2), p=0.023 | -3.6 (-18.1 to +10.9), p=0.670 |
| multi1 (6 scenarios) vs E4B untrained | +32.8 (+25.0 to +41.1), p<0.001 | +39.1 (+30.4 to +50.0), p<0.001 | +28.6 (+18.1 to +40.0), p<0.001 |
| pilot3 (s3 only) vs E4B untrained | +24.1 (+18.1 to +30.9), p<0.001 | +28.3 (+17.7 to +41.7), p<0.001 | +21.4 (+14.6 to +27.8), p<0.001 |

Notes: s3 is a single scenario and is included in 'all' and 'seen by multi1' but not tested alone.
Hard probes: 1 repeat per model; earned probes: 2 repeats. A p-value below 0.05 with an interval that
excludes 0 is read as a difference; wide intervals mean the data cannot separate the models.
