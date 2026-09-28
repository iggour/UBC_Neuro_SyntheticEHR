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

### System prompt

```
You are a senior neurologist / neuro-oncologist designing a FICTIONAL patient for a synthetic
medical record dataset. No real person may be described. Produce a Canonical Facts Sheet as JSON.

Rules:
1. Every field in the provided disease module must be filled with a concrete, clinically coherent value.
2. Values must be internally consistent (anatomy <-> symptoms <-> exam findings <-> imaging <-> pathology/genetics <-> treatment).
3. Give exact dates for all timeline events; dates must be in chronological order.
4. differential_diagnoses_excluded must contain only diagnoses that were considered and ruled out,
   each with the specific evidence used to exclude it. Never include the final diagnosis itself.
5. For structural-lesion diseases, include a three-dimension lesion size. For neurodegenerative
   diseases, do NOT include lesion size; describe atrophy pattern instead.
6. Scale scores and drug doses must be attached to a date.
7. Output JSON only.
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
For consultation notes, ALL of the following sections must appear, in this order, even if brief.
Never drop a section because it seems unrelated to the diagnosis. If a section is empty, write
an explicit statement such as "Past surgical history: none".
 1. Reason for referral / Chief complaint
 2. History of Present Illness (chronological, with dates)
 3. Past Medical History
 4. Past Surgical History
 5. Medications (with reconciliation source and adherence)
 6. Allergies
 7. Social History (occupation, living situation, family support, finances/insurance,
    language needs if any, substance use)
 8. Family History
 9. Physical Examination (vitals; functional status; focused specialty exam; other systems)
10. Investigations (imaging, laboratory with actual values and units, pathology/molecular/genetic)
11. Assessment and Plan (diagnostic reasoning including the differential and how each alternative
    was excluded; treatment options discussed; consent process and patient/family priorities;
    supportive care; follow-up)

FACT DISCIPLINE
- The Canonical Facts Sheet is the single source of truth. Copy anchored values exactly
  (dates, sizes, locations, scores, doses, genetic results, diagnoses).
- Never invent a value that contradicts the sheet. If you need a detail the sheet does not
  contain, choose one that is clinically plausible and consistent with everything else, and keep it
  identical in any later mention.
- When an earlier document is provided, restate its key findings accurately; do not alter them.
- Do not write placeholders such as "not mentioned" or "TBD".

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
| 日期时间线单调递增、无冲突 | 抽取所有日期,按事件排序 |
| 药物名称与剂量在同一时间点一致 | 药物词表 + 剂量正则 |
| 量表分数与 Facts Sheet 一致 | 按量表名抽取分数 |
| 最终诊断/分级/分子结果一致 | 字符串比对 |
| 鉴别诊断列表不含最终诊断 | 集合差检查 |
| 11个章节是否齐全 | 标题匹配 |

需要人工/LLM判断的部分: 解剖—症状是否合理、鉴别诊断推理是否成立、治疗方案是否符合指南。

---

## 版本记录

- v1 (2026-09-27): 初版。相对于最早的手写 demo v1,新增"文书骨架"章节要求与"事实纪律"规则。
