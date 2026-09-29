# Layer 2 — Disease Module: 多发性硬化(多灶炎症、复发缓解)

- 日期: 2026-09-29(从 canonical_facts_template_v1_modules_stroke_ms_pd.md 拆分)
- 类型: B 多灶炎症、复发缓解(唯一一个既非局灶结构病变、也非单纯退行性的类型;时间维度是核心)
- 配套: `layer1_general_template.md`(通用层)、`layer3_guidelines/ms.md`(待建)
- 参考标准: 2024年修订版McDonald标准(Lancet Neurol 2025)

| 字段 | 说明 |
|---|---|
| attack_history | 每次发作的日期、部位、症状、治疗、恢复程度;含既往可能的发作 |
| onset_pattern | relapsing-remitting / primary progressive / CIS |
| EDSS | 带日期(锚定)。真实病例中量表出现率仅 32% |
| MRI_lesion_counts_by_region | 五个区域: periventricular / cortical-juxtacortical / infratentorial / spinal cord / optic nerve,每区的数量与代表性病灶大小(锚定) |
| MRI_activity | 钆增强病灶数量、新发 T2 病灶数量、对比时间 |
| MRI_advanced_markers | central vein sign 比例、paramagnetic rim lesion 数量(选填) |
| CSF | 细胞数、蛋白、寡克隆带(OCB)、kappa 游离轻链(kFLC)指数(>6.1 为阳性)、IgG 指数 |
| serum_antibodies | AQP4-IgG、MOG-IgG(细胞法) |
| differential_excluded | NMOSD、MOGAD、ADEM、结节病、B12 缺乏、梅毒、SLE/血管炎、小血管病等,每项附排除依据 |
| criteria_statement | 2024 McDonald:空间多发(DIS,五区域逐一列出是否满足)、时间多发(DIT,可由 OCB/kFLC 满足)及诊断结论 |
| DMT_decision | 药物选择、筛查项目(乙肝、HIV、VZV、免疫球蛋白、JCV如适用)、生育计划、避孕 |
| follow_up_imaging | 基线后 MRI 的新发/增强病灶,NEDA 评估 |

**重要:不要使用 Fazekas 分级。** MS 的白质病灶用上面的分区计数描述;Fazekas 是给小血管性白质高信号设计的,只在鉴别诊断中作为对照提及。

## 已核对并修正的问题

- **DIS五个区域笼统概括**: demo v1只用一句话说"满足空间多发",未逐一列出五个区域各自的情况。已修正为用表格逐区列出(periventricular / cortical-juxtacortical / infratentorial / spinal cord / optic nerve)并分别标注是否满足,呼应layer1的"多组件诊断标准需逐条列出"规则。

## 待核对清单

- [ ] 各分区病灶计数与 2024 McDonald 空间多发的对应关系(目前按5区域、满足2/5即可的口径,需二次确认版本细节)
- [ ] 中央静脉征、顺磁边缘病灶的影像描述习惯
- [ ] ofatumumab等药物在加拿大的用法与筛查项目细节
