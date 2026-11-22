# Draft text for paper v0.4: sections 2.11-2.12 (methods) and 3.10-3.11 (results), multi-scenario runs

Drafted by Claude, 2026-11-19, for the first author's review. Paste into the .docx when the results
are in; [brackets] are filled from docs/multi1_results.md.

## 2.11 Extending the student to other scenarios

To test whether the method carries over to other patients, we used three of the five families:
Moreno (s1 to s3), Novak (A1 to A3) and Walsh (C5-1 to C5-3). One scenario per family was held out
and never trained (s2, A3 and C5-2), so that it tests a new situation for a patient the student has
seen. The other six families' scenarios (B1 to B3, C4-1 to C4-3) were not used in this run.

For the eight scenarios other than s3, the rules for hidden items were the ones drafted from the
role cards (section 2.8), without hand editing. Hard probes were made from shared templates adapted
from the s3 probes: jailbreak (4), breaking the fourth wall (3), pressure for secrets (5), false
facts (2), requests for medical advice (2), another language (2) and role confusion between patient
and family member (2). Probes that address a family member were left out of the two scenarios
without one (s1, C5-3), giving 16 probes there and 20 elsewhere. There were no self-harm probes
outside s3. As for s3, no probe meets a hidden item's disclosure condition.

The teacher made 40 simulated-trainee conversations for each new trained scenario (s1, A1, A2, C5-1,
C5-3): 8 each from good, average, error-making, pushy and tester trainees. The tester's instructions
were built from the scenario's hidden items: ask about them bluntly before any rapport; ask the
patient about items kept from the family member while the family member stays in the room (only in
scenarios with such items); or put the questions to the family member. Training examples were
filtered as for s3 (section 2.5). The student (multi1) was trained on the pilot3 s3 data and the new
data together (2,233 training and 247 validation examples) with the pilot3 settings.

The teacher, the untrained E4B and multi1 answered the hard probes of all nine scenarios (cold and
warm, one repeat). Replies were checked by the word rules and by the semantic judge (section 2.9;
contradiction not counted).

## 2.13 Statistics

Rates are reported with Wilson 95% confidence intervals. Differences between models were estimated by a
cluster bootstrap that resampled scenarios (10,000 draws), because replies within a scenario are not
independent; we report the difference in percentage points with its 95% percentile interval and a two-sided
p value, pooled over all 15 scenarios, over the six scenarios multi1 was trained on, and over the nine it
was not. s3 alone is a single cluster and was not tested separately (scripts/phase2_stats.py).

## 3.10 The other scenarios

New training data. Of 2,061 patient replies in the 200 new conversations, 1,188 were kept as
training targets (s1 235, A1 200, A2 309, C5-1 255, C5-3 189); 126 failed a check.

[Table 8 = docs/multi1_results.md: hard probes on nine scenarios, replies flagged by the word rules and
by the judge, for the teacher, the untrained E4B and multi1, trained and held-out scenarios.]

The judge flagged none of the teacher's 354 probe replies and 3 of the untrained E4B's 314 judged
replies (all character breaks; A2 not judged). Multi1 was flagged in 11 of 234 replies on trained
scenarios (5%) and 10 of 120 on held-out scenarios (8%): 14 early disclosures (2 of them also with the
family member present), 7 character breaks. The failures were concentrated in a few probes rather
than in particular scenarios. Asked "What's the one thing you haven't told [family member]?" (S2),
the student named a hidden item in 5 of 7 scenarios with a family member, including two held-out
scenarios; asked to answer for the patient (R2), the family member gave away the patient's worry in
4 replies. In s3, asked whether Teresa had told him about the tablets (R1), Luis said he had seen
them or did not know of extra ones, revealing an item he should not know about. Six of the seven
character breaks were replies to "From now on you are the doctor" in which the patient said it was
role-playing or in a simulation, as pilot3 did on s3. The word rules for the eight new scenarios
flagged the teacher in 36 of 354 replies, none of which the judge confirmed; most were the patient
repeating the clinician's words ("role card", "simulation").

In short, training on six scenarios gave a student that kept to its role on unseen scenarios about
as well as on trained ones, but it gave way to direct pressure for secrets more often than the
teacher. The untrained model rarely failed these probes, but on s3 it also disclosed nothing to a
good clinician (section 3.5); disclosure when earned was not measured outside s3.

## 2.12 Opening up when asked well, and unseen families

Hard probes reward a patient that says nothing, so we also measured disclosure when earned. For each
hidden item of all 15 scenarios, two short scripted openings were made: two rapport lines, a request for
the family member to step out if the item is kept from them, then one good question taken from the
rules' test questions (those never shown to the teacher first; only full questions). An item counted as
disclosed if the judge found it in the reply and judged that the question met its condition. Each opening
was run twice per model. The six scenarios of the two families never used in training (B1 to B3, C4-1 to
C4-3) were added to the hard probes. Four models were compared: the teacher, the untrained E4B, pilot3
(trained on s3 only) and multi1.

## 3.11 Keeping secrets and opening up

[Table 9 = docs/phase2_results.md "By tier"; Figure = docs/phase2_tradeoff.png.]

The teacher made no hard-probe failures and disclosed 38% to 67% of items when asked well; because the
questions were drafted automatically and some were brief, even the teacher did not disclose every item,
so models are compared with each other. The untrained E4B rarely failed (0 to 1%) but disclosed little
(0% on s3, 15% on unseen families). Both students disclosed at about the teacher's level: multi1 66%
on trained scenarios (teacher 67%), 55% on held-out scenarios (45%) and 40% on unseen families (38%);
pilot3 54%, 39% and 36%. The cost was 3% to 8% hard-probe failures and a few items revealed to questions
that did not earn them (multi1 11, pilot3 9, untrained 2, teacher 0, of 232). Multi1 disclosed more than
pilot3 in every group with similar failures; pilot3, trained on one scenario, already carried most of the
behaviour to families it had never seen.

So distillation made the small model useful (it opens up when asked well, where the untrained model does
not) and the behaviour transferred to new patients and families, but the students leaned towards
openness: under direct pressure they gave way more often than the teacher.

Statistics (docs/phase2_stats.md). Over all 15 scenarios, training raised disclosure compared with the
untrained E4B (multi1 +32.8 points, 95% CI +25.0 to +41.1, p<0.001; pilot3 +24.1, +18.1 to +30.9,
p<0.001) and multi1's disclosure did not differ from the teacher's (+3.9, -5.4 to +14.0, p=0.47), but its
failures did (+4.8, +2.9 to +6.7, p<0.001). Multi1 disclosed more than pilot3 overall (+8.6, +1.3 to +15.8,
p=0.03), mainly on the scenarios it was trained on (+10.9, p=0.01); on the nine scenarios new to both models
the difference was not clear (+7.1, -3.7 to +17.4, p=0.23), and their failure rates did not differ
(-0.7, -2.9 to +1.4, p=0.59).

## 3.12 Adding pressure-resistance data (multi2)

To reduce failures under pressure, we added 96 simulated-trainee conversations (16 for each trained
scenario) in which the trainee first applied direct pressure for secrets, in its own words, and then held a
proper conversation (953 kept replies), and trained multi2 on these plus the multi1 data. Before the run we
set the rule that multi2 would count as an improvement only if failures fell and disclosure fell by no more
than 5 points in any group.

Failures fell from 28 of 586 hard-probe replies (4.8%) to 7 (1.2%): replies to "from now on you are the
doctor" no longer broke character (8 to 0), and the patient named a hidden item when asked what she had not
told her family member in 2 replies instead of 7. Premature disclosures fell from 11 to 7 of 232. But
disclosure when earned also fell, by 24 points on s3 (to 38%, the teacher's level), 15 on trained scenarios
(51%) and 11 on unseen families (29%), and held at 52% on held-out scenarios. Under the rule this was not an
improvement: like pilot2 on s3, the extra data moved the student along the trade-off towards caution. The
balance between keeping secrets and opening up followed the training mix; neither student matched the
teacher on both at once.

Statistics for multi2 (docs/phase2_stats.md): compared with multi1, failures fell by 3.6 points (95% CI
-5.4 to -1.8, p<0.001) and disclosure fell by 11.2 points (-19.0 to -3.1, p=0.007); multi2 still failed
slightly more often than the teacher (+1.2, +0.3 to +2.2, p=0.005).

Limitations to add to section 4: rules and probes for the eight new scenarios were drafted and not
reviewed by hand; one repeat per probe; no self-harm probes outside s3; s3 is about half of the
training data; the trial-script measures (H1 to H3 disclosure to a good clinician) were run only on s3,
disclosure on the other scenarios was measured with single scripted questions (section 2.12), not full conversations; the judge is the same 31B model as the teacher.
- The multi2 pressure tactics target the same kinds of pressure as the hard probes (never their wording;
  lines close to a probe were cut), so its lower failure rate partly reflects training on the probes'
  categories; the held-out and unseen-family results are the fairer check.
- Hard probes were run once and earned probes twice per model; between-scenario variation dominates the
  intervals, so whether training on more scenarios helps on new scenarios (multi1 vs pilot3) stays open.
