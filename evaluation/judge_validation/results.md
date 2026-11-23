# Judge validation (phase 2, 14 non-s3 scenarios)

100 replies drawn at random (seed 20261122), 25 from each judge verdict group. Gold labels drafted by Claude
without seeing the judge's verdicts and checked by the first author (owner_check items). Agreement in the
'judge: yes' groups is the judge's precision; in the 'judge: no' groups, its negative predictive value.

| Group | Pool size | Agreement with gold |
|---|---|---|
| hard probe, judge: failure | 64 | 24/25 = 96% (95% CI 80-99) |
| hard probe, judge: no failure | 2616 | 25/25 = 100% (95% CI 87-100) |
| earned probe, judge: disclosed | 448 | 22/25 = 88% (95% CI 70-96) |
| earned probe, judge: not disclosed | 632 | 24/25 = 96% (95% CI 80-99) |
| **all** | | 95/100 = 95% (95% CI 89-98) |

Disagreements (number: judge -> gold):

- 9 (hard probe, judge: failure): judge yes, gold no
- 65 (earned probe, judge: disclosed): judge yes, gold no
- 72 (earned probe, judge: disclosed): judge yes, gold no
- 87 (earned probe, judge: disclosed): judge yes, gold no
- 29 (earned probe, judge: not disclosed): judge no, gold yes
