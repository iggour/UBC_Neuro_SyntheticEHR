# Generation Prompt v1

- 日期: 2026-09-27
- 配套文件: `prompts/canonical_facts_template_v1.md`
- 目的: 让LLM稳定生成"完整、专业、跨文档一致"的合成神经科病历
- 状态: 预实验版本。demo v2 由 Claude 按本 prompt 手动生成,尚未用 API 批量跑通

---

## 流水线设计(两阶段 + 检查)

```
Stage 1  病种模块 + 随机种子  ->  Canonical Facts Sheet (JSON)
Stage 2  Facts Sheet + 文档类型 + (已生成的前序文档)  ->  单份文档
Stage 3  程序化一致性检查(正则/数值比对) + 人工抽查
```

关键点:
- Facts Sheet 是唯一事实来源。每个文档agent每次都重新拿到完整 Facts Sheet,不靠"记忆"。
- 每个文档只负责自己的文体;事实数值一律引用 Facts Sheet。
- 后续文档需要复述前序文档的关键发现(真实会诊记录本来就会总结既往影像/病理),这些复述正是一致性检查点。

---

## Stage 1: 生成 Canonical Facts Sheet

自v2.1demo起，Facts Sheet统一采用以下YAML层级schema（不再是Stage 2里各字段的扁平JSON）。
这个schema的分区参考了病历本身的逻辑分组（presentation / clinical / investigations /
diagnostic_criteria / differential / treatment / medications / functional_status /
safety_and_screening / social），并且末尾固定有一个 `key_consistency_facts` 列表，
用自然语言写出"这份病例里最容易在跨文档生成时被写错/写漂移的几条事实"，供后续一致性
检查的评委agent直接使用，不需要它自己去猜哪些是锚点。

```yaml
patient: {initials, sex, dob, age}
timeline: {YYYY-MM-DD: [event, event, ...], ...}
presentation: {onset, chief_features, symptom_duration}
clinical: {diagnosis, disease_course, relevant_history, examination, severity_scores}
investigations:
  laboratory: {key_results}
  imaging: {modality, findings, lesion_distribution, lesion_count, enhancement, other_key_markers}
  pathology: {diagnosis, grade, key_features}
  molecular: {key_results}
  CSF: {key_results}
diagnostic_criteria: {criteria_name, criteria_version, findings_supporting, findings_not_supporting}
differential:
  - {diagnosis, status: supported/not_supported, evidence}
treatment: {acute, disease_modifying, symptomatic, monitoring, follow_up}
medications: {current, changes}
functional_status: {relevant_scores, residual_deficits, ADL, work, driving}
safety_and_screening: {contraindications, baseline_screening, monitoring_requirements, pregnancy, vaccination, infection_risk}
social: {occupation, language, smoking, family_history}
key_consistency_facts: [fact, fact, fact, ...]
```

对没有意义的字段（比如退行性疾病没有lesion_size，卒中没有molecular），填 "not applicable"
或 "not performed"，不要删掉这个字段本身——保留字段名是为了让不同病种的Facts Sheet结构
可以互相比较、也方便后续写自动化一致性检查脚本时用同一套key去取值。

### System prompt

```
You are a senior neurologist / neuro-oncologist designing a FICTIONAL patient for a synthetic
medical record dataset. No real person may be described. Produce a Canonical Facts Sheet as YAML,
following exactly the schema given to you (see above). Do not add or rename top-level keys.

Rules:
1. Every field in the provided disease module must be filled with a concrete, clinically coherent
   value, or explicitly "not applicable" / "not performed" if genuinely not relevant to this case.
2. Values must be internally consistent (anatomy <-> symptoms <-> exam findings <-> imaging <->
   pathology/genetics <-> treatment).
3. Give exact dates for all timeline events; dates must be in chronological order.
4. differential[].status must be "not_supported" for every diagnosis considered and ruled out,
   with the specific evidence used to exclude it in differential[].evidence. Never include the
   final diagnosis itself as an entry in this list.
5. For structural-lesion diseases, investigations.imaging must include a three-dimension lesion
   size in other_key_markers. For neurodegenerative diseases, do NOT include a lesion size;
   describe the atrophy pattern instead.
6. Every severity score and drug dose must be attached to a date (in clinical.severity_scores,
   medications.current, or the timeline).
7. key_consistency_facts must list, in plain sentences, the specific values that a later document
   or a consistency-checking agent must not contradict (e.g. side/laterality, exact dates that
   fix a sequence, a diagnosis that must never reappear as a differential).
8. Output YAML only.
```

### User prompt 模板

```
Disease module: {brain_tumor | huntington}
Setting: British Columbia, Canada; documents written in 2026
Seed constraints (optional): {age range, sex, presenting symptom, ...}
Required template: <paste canonical_facts_template_v1.md, Layer 1 B + relevant Layer 2 module>
```

---

## Stage 2: 生成单份文档

### System prompt(固定部分)

```
You are writing one clinical document for a FICTIONAL patient in a synthetic dataset.
You will receive (a) a Canonical Facts Sheet, (b) the document type to write, and
(c) any earlier documents for this patient.

DOCUMENT COMPLETENESS
For consultation notes, ALL of the following sections must appear, numbered in this order, even
if brief. Never drop a section because it seems unrelated to the diagnosis. If a section is empty,
write an explicit statement such as "Past surgical history: none".
 1.  Reason for Referral
 2.  History of Present Illness (chronological, with dates)
 3.  Past Medical History
 4.  Past Surgical History
 5.  Medications (with reconciliation source and adherence)
 6.  Allergies
 7.  Social History (occupation, living situation, family support, finances/insurance,
     language needs if any, substance use)
 8.  Family History
 9.  Physical and Neurological Examination (vitals; functional status; focused specialty exam;
     other systems; disease-specific scales reported as clearly separate instruments -
     never merge two different scales, e.g. UHDRS and PBA-s, into one score or one paragraph)
10.  Investigations, with subsections:
     10.1 Laboratory
     10.2 Neuroimaging
     10.3 Pathology
     10.4 Molecular / Genomic
     10.5 CSF
     Write "Not applicable" or "Not performed" for any subsection not relevant to this case;
     never omit the subsection heading.
11.  Assessment (diagnostic reasoning; the differential and, for each alternative considered,
     the specific evidence used to exclude it - never list the final diagnosis itself as an
     excluded differential; treatment options discussed; consent process and patient/family
     priorities)
12.  Plan (supportive care; monitoring; follow-up)

FACT DISCIPLINE
- The Canonical Facts Sheet is the single source of truth. Copy anchored values exactly
  (dates, sizes, locations, scores, doses, genetic results, diagnoses).
- Never invent a value that contradicts the sheet. If you need a detail the sheet does not
  contain, choose one that is clinically plausible and consistent with everything else, and keep it
  identical in any later mention.
- When an earlier document is provided, restate its key findings accurately; do not alter them.
- Do not write placeholders such as "not mentioned" or "TBD".
- Do not use bracket placeholders for clinician names (e.g. "[Radiologist]"). Invent a specific
  fictitious full name for every signing clinician and keep that name consistent for that role
  across documents for the same patient.
- Drug starting doses and titration schedules must match the real prescribing information for
  that drug (starting dose, interval before increasing, when divided dosing is required, when
  genotyping or other safety testing is required). Verify rather than estimate from general
  impression when the drug has a well-defined titration schedule.
- When discussing implications of a diagnosis for insurance, employment, or legal protections
  (e.g. genetic discrimination, disability accommodation), describe the topic in general terms
  and note that a specialist (genetic counsellor, social worker, legal resource) will cover
  specifics, rather than citing a specific named law or policy, unless the person writing the
  prompt explicitly supplies the correct, current, jurisdiction-specific reference.
- For any named diagnostic criteria (McDonald, MDS-PD, TOAST, WHO CNS tumour classification,
  etc.), when the criteria require checking multiple discrete components (e.g. dissemination in
  space across several anatomical regions), enumerate each component explicitly (e.g. as a table
  or list) and state whether it is met, rather than asserting the overall conclusion in one
  sentence.

STYLE
- Write as a real clinician would for this document type and setting (Canadian, 2026).
  Imaging reports: concise, objective, Technique / Findings / Impression.
  Consultation notes: full narrative with discussion and plan.
- Use fictitious identifiers only (initials, fake PHN, fake accession numbers, fictional
  clinician names). Do not use real people, real patients, or real institutions' patient data.
- Include realistic imperfections real notes have (brief phrases, standard abbreviations),
  but never clinical contradictions.
```

### User prompt 模板

```
Document type: {MRI report | neuro-oncology consultation | movement disorders consultation | ...}
Document date: {YYYY-MM-DD}
Canonical Facts Sheet:
{JSON from Stage 1}
Earlier documents for this patient:
{none | full text of earlier documents}
Write the document now.
```

---

## Stage 3: 一致性检查(可程序化的部分)

| 检查项 | 方法 |
|---|---|
| 病灶三径线在各文档中相同 | 正则抽取 "x × y × z cm" 并比对 |
| 病灶位置(左/右、脑叶/回)一致 | 关键词表比对 + 左右冲突检测 |
| 日期时间线单调递增、无冲突 | 抽取所有日期,按事件排序,与 Facts Sheet 的 timeline 比对 |
| 药物名称与剂量在同一时间点一致 | 药物词表 + 剂量正则,对照 medications.current / medications.changes |
| 量表分数与 Facts Sheet 一致 | 按量表名抽取分数,对照 clinical.severity_scores(注意不同量表不能互相混淆,例如UHDRS与PBA-s是两个独立工具) |
| 最终诊断/分级/分子结果一致 | 字符串比对 clinical.diagnosis 与 investigations.pathology/molecular |
| 鉴别诊断列表不含最终诊断 | 集合差检查 differential[].diagnosis 与 clinical.diagnosis |
| 12个章节(含10.1-10.5子节)是否齐全 | 标题匹配 |
| key_consistency_facts 逐条核对 | 把 Facts Sheet 里这份清单直接作为检查项列表,逐条在生成文档里搜索/比对,不需要另外设计检查逻辑 |

需要人工/LLM判断的部分: 解剖—症状是否合理、鉴别诊断推理是否成立、治疗方案是否符合指南、
诊断标准的多组件判断(如McDonald标准五个区域)是否被逐一列出而不是笼统一句话概括。

---

## 版本记录

- v1 (2026-09-27): 初版。相对于最早的手写 demo v1,新增"文书骨架"章节要求与"事实纪律"规则。
- v1.1 (2026-09-28): 根据五份demo(脑肿瘤/亨廷顿/卒中/MS/帕金森)人工核对后的六处修正,更新为:
  (1) 12节编号格式(拆分Assessment/Plan为11/12,Investigations拆分10.1-10.5子节);
  (2) Facts Sheet改为YAML层级schema,末尾固定key_consistency_facts列表;
  (3) 事实纪律新增: 禁用方括号占位签名、药物起始剂量须核对说明书、涉及具体法律/政策名称的表述
      改为通用描述、多组件诊断标准需逐条列出而非一句话概括、不同评分量表不能混在一段。
