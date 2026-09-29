# Layer 2 — Disease Module: 亨廷顿病(退行性/遗传确诊类)

- 日期: 2026-09-29(从 canonical_facts_template_v1.md 拆分)
- 类型: C 退行性/以临床诊断为主
- 配套: `layer1_general_template.md`(通用层)、`layer3_guidelines/huntington.md`(待建,优先级最高——见下方剂量核对记录)

| 字段 | 说明 |
|---|---|
| atrophy_pattern | 萎缩部位与程度(不要求毫米数值,退行性病种 lesion_size 为0%) |
| imaging_modalities | array |
| UHDRS | 四个子部分,须分开报告,不与PBA-s或认知筛查混为一谈: Total Motor Score(/124)、Total Functional Capacity(/13)、Functional Assessment(/25)【待核对完整条目结构】 |
| PBA_s | Problem Behaviours Assessment for HD short form,独立于UHDRS的量表(irritability、apathy等分项) |
| cognitive_screen | MoCA、SDMT、语言流畅性等,独立于UHDRS和PBA-s |
| genetic_confirmation | {gene: HTT, cag_repeat_alleles, interpretation} **必填**(真实病例中80%出现,是确诊性检测) |
| cag_interpretation_reference | ≤26 正常; 27-35 中间; 36-39 不完全外显; ≥40 完全外显【待核对】 |
| family_history_structured | {inheritance_pattern, affected_relatives, at_risk_relatives, prior_counselling} **必填**(真实病例中60%) |
| symptomatic_treatment | 药物、起始剂量、监测项 |

## 已核对并修正的问题(记录留档,避免重复犯错)

- **UHDRS/PBA-s/认知量表混杂**: demo v1曾把三种不同工具的分数混在同一段落,已修正为分开列出,并在生成规则中明确标注"不同评分量表不能混在一段"(见 layer1 事实纪律)
- **tetrabenazine起始剂量错误**: demo v1写成"12.5mg daily起始,按周递增",未体现分次给药要求。已核实FDA说明书,正确方案为:第1周12.5mg每日一次(晨服);第2周起25mg/day(12.5mg一天两次);之后每周递增12.5mg;37.5-50mg/day须分三次给药,单次最大25mg;超过50mg/day须查CYP2D6基因型。查证日期2026-09-28,来源: FDA处方信息/说明书(检索多个来源交叉确认)。
- **政策/法律具体名称**: demo v1曾具体引用某国法案名称讨论遗传信息保护,已改为通用表述,交由遗传咨询师说明细节。

## 待核对清单

- [ ] UHDRS四个子部分的具体条目与评分方式(目前只核实了总分结构,未逐条核对)
- [ ] tetrabenazine监测项是否符合本地(加拿大)指南,是否与FDA说明书一致
