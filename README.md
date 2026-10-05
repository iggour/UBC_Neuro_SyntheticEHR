# UBC Neuro Synthetic EHR Project

**Goal:** Explore whether canonical-fact-driven, multi-layer prompting can generate realistic,
internally-consistent synthetic neurology patient records (no real patients involved), and test
whether the same prompt design transfers across different LLMs.

This is an early-stage pilot. Nothing here uses or was derived from real patient data — all
"demo" cases are entirely fictional, generated from invented canonical facts.

---

## How the prompt system is structured (read this first)

Generating one synthetic case means assembling **3 layers + 1 orchestration file** into a single
prompt. This is the part that matters if you're trying to reproduce or run this on another model.

```
prompts/
├── layer1_general_template.md          Layer 1 — disease-agnostic: the 12-section document
│                                        skeleton, universal fields, YAML Canonical Facts Sheet
│                                        schema, and cross-disease "fact discipline" rules
│                                        (e.g. no bracket placeholders for clinician names,
│                                        verify real drug titration schedules, etc.)
│
├── layer2_disease_modules/             Layer 2 — disease-specific fields (one file per disease).
│   ├── brain_tumor.md                  Structural lesion type: location, size, molecular markers
│   ├── huntington.md                   Genetic/degenerative type: CAG repeats, UHDRS, no lesion size
│   ├── stroke.md                       Acute structural type: NIHSS, vascular territory, TOAST
│   ├── ms.md                           Relapsing/multifocal type: McDonald criteria, lesion regions
│   └── parkinson.md                    Clinical-diagnosis type: MDS-PD criteria, LEDD, no imaging lesion
│
├── layer3_guidelines/                  Layer 3 — verified clinical reference values that constrain
│   ├── common/                         what Layer 2 fields are allowed to say. Kept separate from
│   │   └── medication_safety.yaml.md   Layer 1/2 so it can be updated independently as guidelines
│   └── huntington/                     change, without touching the prompt logic itself.
│       ├── diagnosis.yaml.md           Currently only Huntington disease is covered (pilot).
│       └── treatment.yaml.md           Other 4 diseases: Layer 3 not written yet.
│
└── generation_prompt_v1.md             Orchestration: how to combine Layer 1 + Layer 2 (+ Layer 3
                                         when available) into Stage 1 (generate a Canonical Facts
                                         Sheet) and Stage 2 (generate the actual document text).
```

**To generate one case, concatenate:** `layer1_general_template.md` + the relevant file in
`layer2_disease_modules/` + (if available) the relevant files in `layer3_guidelines/`, following
the system-prompt template in `generation_prompt_v1.md`.

Files ending in `.yaml.md` are drafts: the content is YAML but kept in a `.md` wrapper with notes
explaining sourcing, so a human can review before it's treated as final. Not yet converted to
plain `.yaml`.

---

## Data pipeline (how the real-case statistics behind Layer 2 were derived)

Source dataset: `OpenMed/multicare-cases` (Hugging Face), openly licensed case reports originally
from PubMed Central. No real-time patient data; no institutional data-use agreement required for
this dataset (unlike PhysioNet/MIMIC, which was explored but requires credentialing).

Run in this order:

1. **`scripts/filter_neuro.py`** — stream-filters ~300 neurology-related cases by keyword from the
   full MultiCaRe dataset (some keywords position-restricted to reduce false positives from
   incidental mentions, e.g. "stroke" mentioned only as a ruled-out differential).
   → `data/raw/neuro_cases_raw.json`

2. **`scripts/split_by_disease.py`** — splits into 6 disease-keyword buckets.
   → `data/by_disease/{disease}_cases.json`

3. **`scripts/llm_annotate.py`** — LLM-based (DeepSeek) classification per case: is this a real
   single-patient case (not a review article)? Is the neuro condition the primary complaint (not
   just an incidental past-history mention)? Plus 10 more fields (scales used, genetic testing,
   onset pattern, differential diagnosis present, family history, etc.)
   → `{disease}_cases_llm_annotated.json` (full) / `{disease}_cases_valid_primary.json` (filtered)

4. **`scripts/extract_canonical_facts.py`** — LLM extraction of 17 structured fields per case
   (chief complaint, anatomical location, scales with scores, medications, differential diagnoses
   excluded with evidence, etc.)
   → `{disease}_canonical_facts.json`

5. **`scripts/summarize_facts.py`** — aggregates non-empty rate and top values per field per
   disease. This is what Layer 2's field choices and "real-world distribution" notes are based on.

**Result after filtering (Sept 2026):**

| Disease | Raw filtered | LLM-verified valid + primary |
|---|---|---|
| Stroke | 51 | 31 |
| Multiple sclerosis | 67 | 56 |
| Parkinson's | 30 | 24 |
| Alzheimer's | 20 | 9 (not yet modeled — see below) |
| Huntington's | 6 | 5 |
| Brain tumor | 132 | 115 |
| **Total** | **306** | **240** |

**Key findings that shaped the Layer 2 design (see individual module files for detail):**
- `lesion_size` is 0% non-empty for Parkinson's/Alzheimer's/Huntington's (degenerative diseases
  have no measurable focal lesion) vs. 23-60% for stroke/brain tumor/MS (structural diseases) —
  this is why Layer 2 has distinct "structural" vs. "degenerative" field sets per disease.
- `genetic_testing` is 80% non-empty for Huntington's (it's the confirmatory test) vs. <25% for
  other diseases (incidental/supportive only).
- Family-history non-empty rate tracks heritability: stroke 3% < Parkinson's 33% < Alzheimer's
  44% < Huntington's 60%.

**Alzheimer's is not yet built out as a Layer 2 module.** Real sample size is only 9 cases, one of
which was actually Dementia with Lewy Bodies, not AD. Needs updated diagnostic-criteria research
(current AD criteria rely heavily on biomarkers) before writing the module — deliberately deferred
to a second round rather than modeled on insufficient data.

---

## Demos (`demos/`)

Five hand-written (not yet API-generated) example cases, one per disease, each following the
Layer 1 skeleton with the Layer 2 fields filled in, plus a YAML Canonical Facts Sheet at the end
of each file (the ground truth that later documents for the same patient should stay consistent
with).

- `brain_tumor_demo_v2.md`, `huntington_demo_v2.md`, `stroke_demo_v2.md`, `ms_demo_v2.md`,
  `parkinson_demo_v2.md` — current versions (v2.1), each with 2-3 longitudinal documents per
  patient (e.g. initial imaging report + follow-up consultation) to demonstrate cross-document
  fact consistency, not just single-document realism.

- `ds_test_huntington_*` — DeepSeek API cross-model test outputs (see below).

**Known issue flagged by a clinical expert reviewer:** the Huntington demo includes an MRI
report. In real practice, imaging is not part of the standard diagnostic pathway for Huntington's
(diagnosis is genetic/CAG-repeat-based); imaging is supportive/research-context only. This is
noted in `layer2_disease_modules/huntington.md` as a pending fix, not yet corrected in the demo.

---

## Cross-model test: does the prompt work without Claude-specific context?

Ran via DeepSeek API (`scripts/test_deepseek_huntington.py` + `_stage2.py`) to check whether the
Layer 1+2(+3) prompt produces correct results on a different model, independent of this chat's
accumulated context — i.e. a cleaner test of the *prompt itself*, not of "Claude remembering
earlier corrections."

**A/B test: with vs. without Layer 3 guidance**, same Layer 1 + Layer 2 (Huntington) input:

- **Without Layer 3:** tetrabenazine titration plan omitted the CYP2D6 genotyping requirement
  above 50mg/day entirely, and proposed titrating up to 75mg/day without that safety check.
- **With Layer 3:** correctly included the CYP2D6 requirement before exceeding 50mg/day, and the
  model actually wrote a scene where genotyping was ordered before the dose increase.

This is the first concrete evidence that the Layer 3 guidance layer changes model behavior in the
intended direction, not just a theoretical nice-to-have. See:
`demos/ds_test_huntington_with_layer3.yaml` vs. `demos/ds_test_huntington_no_layer3.yaml`.

Bilingual output was also tested: English note generated from the Facts Sheet
(`ds_test_huntington_note_en.md`), then translated (not re-generated) into Chinese
(`ds_test_huntington_note_zh.md`) with a separate translation-only prompt, to test whether numbers/
doses/dates survive translation unchanged.

---

## What's deliberately NOT done yet (and why)

- **No real patient data anywhere.** By design. Any future extension involving real clinical data
  would need separate ethics review — not yet pursued, deliberately.
- **No fine-tuning, no local model deployment yet.** Everything so far is prompting (API calls),
  no training. Local deployment on institutional compute is a separate open question with the
  supervisor, not started.
- **No automated/programmatic consistency checker yet.** Current consistency checking is manual
  (human review against the Canonical Facts Sheet). A scripted checker (regex/value extraction +
  comparison) is a planned next step, not built.
- **No "reasoning agent" (e.g., inferring what exam to order next, or inferring a likely genetic
  result from indirect evidence) is built.** This is explicitly staged for *after* the generation
  side is validated — reasoning quality can't be meaningfully tested on a generator whose outputs
  aren't yet known to be internally consistent and clinically coherent.
- **Layer 3 guidance only exists for Huntington's disease.** The other 4 diseases' Layer 2 modules
  were written using general domain knowledge but have not had their specific dosing/criteria
  claims individually verified against a primary source the way Huntington's tetrabenazine dosing
  was. Treat Layer 2 claims for stroke/MS/Parkinson's/brain tumor as drafts pending the same
  verification pass.

---

## Environment

- Python 3.12; dependencies: `datasets`, `pandas`, `openai` (used for the OpenAI-compatible
  DeepSeek API, not for OpenAI itself)
- API key expected in environment variable `DEEPSEEK_API_KEY`
