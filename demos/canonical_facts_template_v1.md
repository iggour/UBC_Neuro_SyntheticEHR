# Canonical Facts 分层模板 v1

- 日期: 2026-09-27
- 数据依据: MultiCaRe 神经科病例(LLM精筛后240条)的字段统计,见 `scripts/summarize_facts.py`
- 适用病种: 脑肿瘤(结构病变类)、亨廷顿病(退行性/遗传确诊类)
- 状态: 预实验版本,标注【待核对】的条目需要临床专业判断后再定稿

---

## 设计原则

1. **两层结构**
   - 第一层(通用层): 文书骨架 + 通用字段。与病种无关,任何专科会诊记录都必须完整。
   - 第二层(病种模块): 体现该病种特色的字段。病种之间不能互换(例如退行性疾病没有 lesion_size)。
2. **锚定字段 vs 自由表达字段**
   - 锚定字段(canonical anchors): 一旦设定,所有文档必须保持一致,不允许漂移。
   - 自由表达字段: 措辞、叙述风格可以按文档类型和专科习惯自由变化。
3. **缺失也要显式处理**: 章节标题不能省略;没有内容时写"None"/"Nil"/"Not applicable",不要整段消失。

---

## 第一层 A: 文书骨架(11个必备章节)

1. Reason for referral / Chief complaint
2. History of Present Illness(含发病时间线)
3. Past Medical History
4. Past Surgical History
5. Medications(含核对来源、依从性)
6. Allergies
7. Social History(职业、居住、家庭支持、经济、语言需求、物质使用)
8. Family History
9. Physical Examination(生命体征 + 功能状态 + 专科查体 + 其他系统)
10. Investigations(影像/实验室/病理/分子检测,须给出具体数值)
11. Assessment and Plan(诊断推理含鉴别诊断、治疗讨论与知情同意过程、支持治疗、随访)

## 第一层 B: 通用字段

| 字段 | 类型 | 备注 |
|---|---|---|
| patient_demographics | {age, sex, dob(虚构)} | 锚定 |
| chief_complaint | string | 锚定 |
| onset_pattern | enum: acute / subacute / chronic / progressive / relapsing-remitting | 锚定 |
| symptom_duration_before_presentation | string | 锚定 |
| key_symptoms | array | 锚定 |
| final_diagnosis | string | 锚定 |
| differential_diagnoses_excluded | array of {diagnosis, evidence_for_exclusion} | 锚定。见下方"已知问题" |
| medications | array of {drug, dose, start_date, response_or_side_effect} | 锚定(按时间点) |
| timeline_events | array of {date, event} | 锚定,所有文档日期必须自洽 |
| multidisciplinary_team | array | 自由表达 |
| followup_plan | {interval, tests, referrals} | 自由表达 |

### 已知问题(来自预实验)

原字段 `differential_diagnoses_considered` 会把"最终确诊的疾病本身"误算进去。
修正后的字段名与定义:

> `differential_diagnoses_excluded`: 文中明确考虑过、但最终被排除的其他诊断。
> 不包括最终确诊的疾病本身,也不包括该病的同义词/亚型。
> 若没有明确的排除性讨论,返回空数组,不要推测。

---

## 第二层 A: 结构性病变模块(脑肿瘤)

| 字段 | 说明 |
|---|---|
| anatomical_location | 具体到脑叶/回/结构(锚定) |
| lesion_size | 三径线(cm),锚定;真实病例中约40%不给精确数值,见"软约束" |
| lesion_characteristics | {signal, enhancement_pattern, necrosis, edema, mass_effect, midline_shift_mm, diffusion, perfusion} |
| relation_to_eloquent_structures | 与运动皮层/皮质脊髓束/语言区/视路的关系 |
| imaging_modalities | array |
| histopathology | 病理类型与WHO分级(锚定) |
| molecular_markers | IDH、MGMT、1p/19q、TERT、EGFR、+7/-10、H3 K27M、BRAF 等(锚定)【待核对是否完整】 |
| location_specific_functional_assessment | 病灶位置触发的功能评估:运动区→肌力(MRC);视路→BCVA/视野;语言区→语言评估 |
| extent_of_resection | 术后MRI(72小时内)结论 |
| performance_status | KPS / ECOG |

## 第二层 B: 退行性/遗传确诊模块(亨廷顿)

| 字段 | 说明 |
|---|---|
| atrophy_pattern | 萎缩部位与程度(不要求毫米数值,退行性病种 lesion_size 为0%) |
| imaging_modalities | array |
| UHDRS | 四个子部分: motor(总分/124)、cognitive、behavioral、functional(含TFC/13)【待核对具体条目】 |
| cognitive_screen | MoCA、SDMT、语言流畅性等 |
| behavioral_assessment | PBA-s 或等价工具;抑郁/自杀风险筛查(PHQ-9、C-SSRS) |
| genetic_confirmation | {gene: HTT, cag_repeat_alleles, interpretation} **必填**(真实病例中80%出现) |
| cag_interpretation_reference | ≤26 正常; 27-35 中间; 36-39 不完全外显; ≥40 完全外显【待核对】 |
| family_history_structured | {inheritance_pattern, affected_relatives, at_risk_relatives, prior_counselling} **必填**(真实病例中60%) |
| symptomatic_treatment | 药物、起始剂量、监测项(如 tetrabenazine 需抑郁/QTc监测) |

---

## 锚定字段清单(跨文档必须一致)

- 患者标识、年龄、性别、日期
- 病灶位置与大小(术前)、关键影像描述
- 最终诊断、病理分级、分子/遗传结果
- 时间线上的所有日期
- 各时间点的量表分数(必须带日期)
- 各时间点的药物与剂量
- 鉴别诊断及其排除依据

## 自由表达字段

- 叙述措辞、章节内部的写作风格
- 查体描述的具体句式
- 社会史的具体细节(一旦写出,后续文档必须保持一致)

---

## 真实分布软约束(来自240条真实病例统计)

注意: 这些数字来自已发表的病例报告,天然偏向疑难/罕见病例,不代表日常门诊分布。

| 观察 | 数据 | 生成时的用法 |
|---|---|---|
| lesion_size 在结构病变类中的出现率 | 脑肿瘤 60%,卒中 23%,MS 14% | 影像/病理文档给精确数值;非影像文档可用近似表述 |
| 退行性病种 lesion_size | 帕金森/AD/亨廷顿均为 0% | 退行性模块不设该字段 |
| genetic_testing | 亨廷顿 80%,其他病种 <25% | 亨廷顿必填;其他病种按条件触发 |
| family_history 出现率 | 卒中 3% < 帕金森 33% < AD 44% < 亨廷顿 60% | 遗传成分越强,越应详细结构化 |
| 脑肿瘤功能评估 | 高频为 BCVA/视野,非笼统严重度量表 | 病灶位置决定评估类型 |

## 待你(放射科/临床)核对的清单

- [ ] 脑肿瘤分子标记是否覆盖 WHO CNS 分类要求(含 CDKN2A/B 等)
- [ ] 影像报告的序列与描述习惯是否符合北美/国内规范
- [ ] UHDRS 四个子部分的具体条目与评分方式
- [ ] tetrabenazine 的监测项与起始方案是否符合本地指南
- [ ] 社会史中与加拿大医疗体系相关的细节(药物覆盖、驾驶规定、遗传歧视相关法规)是否表述准确
