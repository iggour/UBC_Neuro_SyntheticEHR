# Layer 2 — Disease Module: 脑肿瘤(结构性病变类)

- 日期: 2026-09-29(从 canonical_facts_template_v1.md 拆分)
- 类型: A 局灶结构病变
- 配套: `layer1_general_template.md`(通用层)、`layer3_guidelines/brain_tumor.md`(待建)

| 字段 | 说明 |
|---|---|
| anatomical_location | 具体到脑叶/回/结构(锚定) |
| lesion_size | 三径线(cm),锚定;真实病例中约40%不给精确数值,见"真实分布软约束" |
| lesion_characteristics | {signal, enhancement_pattern, necrosis, edema, mass_effect, midline_shift_mm, diffusion, perfusion} |
| relation_to_eloquent_structures | 与运动皮层/皮质脊髓束/语言区/视路的关系 |
| imaging_modalities | array |
| histopathology | 病理类型与WHO分级(锚定) |
| molecular_markers | IDH、MGMT、1p/19q、TERT、EGFR、+7/-10、H3 K27M、BRAF 等(锚定)【待核对是否覆盖 WHO CNS 分类要求,如 CDKN2A/B】 |
| location_specific_functional_assessment | 病灶位置触发的功能评估:运动区→肌力(MRC);视路→BCVA/视野;语言区→语言评估 |
| extent_of_resection | 术后MRI(72小时内)结论 |
| performance_status | KPS / ECOG |

## 真实分布软约束(来自240条真实病例统计,samples偏向疑难病例,仅供参考)

- lesion_size 在脑肿瘤病例中出现率约60%,其余多用"large"/"small"/"well-defined"等模糊描述
- clinical_scales_used 高频为视功能相关(BCVA、视野),而非笼统严重度评分——提示病灶位置决定伴随的功能评估类型
- genetic_testing(分子标记)出现率约13%,但在真实临床工作中,高级别胶质瘤应常规送检

## 待核对清单

- [ ] 分子标记是否覆盖 WHO CNS 分类(2021第5版)要求,含 CDKN2A/B 纯合缺失等
- [ ] 影像报告的序列与描述习惯是否符合北美/国内规范
