# Layer 1: 通用层(文书骨架 + 通用字段)

- 日期: 2026-09-29(从 canonical_facts_template_v1.md 拆分整理)
- 适用范围: 全部病种,不含任何病种特异性内容
- 配套: `layer2_disease_modules/*.md`(病种模块)、`layer3_guidelines/*.md`(指南层,待建)、`generation_prompt_v1.md`(拼接与生成流程)

---

## 设计原则

1. **两层结构**
   - 第一层(本文件): 文书骨架 + 通用字段。与病种无关,任何专科会诊记录都必须完整。
   - 第二层(`layer2_disease_modules/`): 体现该病种特色的字段。病种之间不能互换。
2. **锚定字段 vs 自由表达字段**
   - 锚定字段(canonical anchors): 一旦设定,所有文档必须保持一致,不允许漂移。
   - 自由表达字段: 措辞、叙述风格可以按文档类型和专科习惯自由变化。
3. **缺失也要显式处理**: 章节标题不能省略;没有内容时写"None"/"Nil"/"Not applicable",不要整段消失。

---

## 文书骨架(12节编号格式,v1.1)

1. Reason for Referral
2. History of Present Illness(含发病时间线)
3. Past Medical History
4. Past Surgical History
5. Medications(含核对来源、依从性)
6. Allergies
7. Social History(职业、居住、家庭支持、经济、语言需求、物质使用)
8. Family History
9. Physical and Neurological Examination(生命体征 + 功能状态 + 专科查体 + 其他系统;不同评分量表须分开列出,不能混在同一段)
10. Investigations,含子节:
    - 10.1 Laboratory
    - 10.2 Neuroimaging
    - 10.3 Pathology
    - 10.4 Molecular / Genomic
    - 10.5 CSF
    (不适用的子节写"Not applicable"/"Not performed",标题不能省略)
11. Assessment(诊断推理含鉴别诊断及排除依据、治疗讨论与知情同意过程)
12. Plan(支持治疗、随访计划)

---

## 通用字段

| 字段 | 类型 | 备注 |
|---|---|---|
| patient_demographics | {age, sex, dob(虚构)} | 锚定 |
| chief_complaint | string | 锚定 |
| onset_pattern | enum: acute / subacute / chronic / progressive / relapsing-remitting | 锚定 |
| symptom_duration_before_presentation | string | 锚定 |
| key_symptoms | array | 锚定 |
| final_diagnosis | string | 锚定 |
| differential_diagnoses_excluded | array of {diagnosis, evidence_for_exclusion} | 锚定,见下方规则 |
| medications | array of {drug, dose, start_date, response_or_side_effect} | 锚定(按时间点) |
| timeline_events | array of {date, event} | 锚定,所有文档日期必须自洽 |
| multidisciplinary_team | array | 自由表达 |
| followup_plan | {interval, tests, referrals} | 自由表达 |

### 字段规则: differential_diagnoses_excluded

> 文中明确考虑过、但最终被排除的其他诊断。不包括最终确诊的疾病本身,也不包括该病的同义词/亚型。
> 若没有明确的排除性讨论,返回空数组,不要推测。

---

## 锚定字段清单(跨文档必须一致)

- 患者标识、年龄、性别、日期
- 病灶位置与大小(如适用)、关键影像描述
- 最终诊断、病理分级、分子/遗传结果
- 时间线上的所有日期
- 各时间点的量表分数(必须带日期,且不同量表不能互相混淆)
- 各时间点的药物与剂量
- 鉴别诊断及其排除依据

## 自由表达字段

- 叙述措辞、章节内部的写作风格
- 查体描述的具体句式
- 社会史的具体细节(一旦写出,后续文档必须保持一致)

---

## 事实纪律(通用规则,适用于所有病种)

- 不使用方括号占位签名(如 "[Radiologist]")。每个签名临床医生都要有具体的虚构全名,同一角色跨文档保持一致。
- 药物起始剂量与滴定方案,须对照该药物真实说明书/权威来源(见对应病种的 `layer3_guidelines/`),不能凭印象估算。
- 涉及具体法律/政策名称(如遗传歧视保护、残疾福利)时,用通用表述("存在相关法律保护但有限制,具体由专科人员说明"),除非明确提供了准确、现行、当地适用的引用。
- 采用多组件诊断标准(如 McDonald、MDS-PD、TOAST、WHO CNS肿瘤分类)时,逐条列出各组件是否满足(可用表格),不要用一句话笼统下结论。

---

## Facts Sheet Schema(YAML,v1.1,适用于所有病种)

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

不适用字段填 "not applicable" / "not performed",不要删掉字段本身。
