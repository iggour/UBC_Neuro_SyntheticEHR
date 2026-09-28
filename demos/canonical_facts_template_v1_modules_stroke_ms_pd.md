# Canonical Facts 模板 v1 增补: 卒中 / MS / 帕金森 三个模块

- 日期: 2026-09-27
- 配套: `prompts/canonical_facts_template_v1.md`(第一层通用层 + 脑肿瘤/亨廷顿模块)与 `prompts/generation_prompt_v1.md`
- 第一层(11章节骨架 + 通用字段)完全沿用,这里只增加第二层病种模块
- 标准依据: 2024 McDonald 标准(Lancet Neurol 2025)、MDS 帕金森临床诊断标准(2015)、加拿大卒中最佳实践指南(2022更新,替奈普酶 0.25 mg/kg,最大25 mg)。标【待核对】的条目需要临床专业判断

## 第二层的三种类型(由原来的两种扩展而来)

| 类型 | 病种 | 特点 | 对应字段设计 |
|---|---|---|---|
| A 局灶结构病变 | 脑肿瘤、**卒中** | 有可定位、可测量的病灶 | 定位 + 大小 + 影像特征 + 症状对应 |
| B 多灶炎症、复发缓解 | **MS** | 没有单一病灶,诊断靠"空间多发 + 时间多发";纵向是核心 | 分区病灶计数 + 时间线 + CSF/抗体 |
| C 退行性/以临床诊断为主 | 亨廷顿、**帕金森** | 影像常正常或只有轻微改变,靠量表和药物反应 | 量表 + 药物方案 + 运动并发症 |

MS 既不像脑肿瘤那样有一个可测量的病灶,也不像帕金森那样几乎不看影像。它需要单独设类型,而且它的"时间维度"是其他病种没有的,最适合展示虚拟纵向研究。

---

## 模块 C1: 卒中(类型 A,急性血管性局灶病变)

| 字段 | 说明 |
|---|---|
| time_last_known_well / symptom_onset / arrival | 精确到分钟,锚定;所有时间指标由它们推出 |
| NIHSS_at_arrival / 24h / discharge / follow-up | 带日期的量表分数(锚定) |
| vascular_territory | 如 左MCA M1;必须与症状侧别、失语/偏瘫类型一致 |
| imaging_acute | CT: ASPECTS、致密动脉征、出血;CTA: 闭塞部位、颈动脉狭窄、侧支;CTP: 核心梗死体积、Tmax>6s 体积、不匹配比 |
| reperfusion_treatment | 静脉溶栓(药物、剂量按体重计算、给药时间)、血管内治疗(方法、mTICI、穿刺/再通时间) |
| door_to_needle / door_to_puncture | 由时间点自动计算,不得与时间线冲突 |
| infarct_MRI | DWI 梗死部位与体积,是否出血转化 |
| etiology_TOAST | 大动脉粥样硬化 / 心源性栓塞 / 小血管 / 其他 / 不明 |
| etiologic_workup | ECG/监测、超声心动图(LVEF、左房、血栓、PFO)、颈动脉/血管影像、血脂、HbA1c |
| secondary_prevention | 抗栓/抗凝药物(含开始日期,依据梗死体积)、他汀及 LDL 目标、血压目标 |
| outcome_90d | mRS、NIHSS、残留缺损(失语类型等) |
| rehabilitation_and_return | 康复、语言治疗、驾驶、工作、抑郁筛查 |

可程序化检查: 时间线单调递增、door-to-needle 计算、偏瘫侧别与病灶侧别相反、给药剂量 = 体重 × 0.25(上限25 mg)。

从真实病例统计得到的观察(注意样本偏向疑难病例): 起病模式 94% 记录为急性;量表出现率 68%;遗传相关信息仅 6%,主要来自线粒体病等特殊病因。生成时可以按"典型心源性栓塞/大动脉粥样硬化/罕见病因"设置病因亚型种子。

## 模块 C2: 多发性硬化(类型 B)

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
| criteria_statement | 2024 McDonald:空间多发(至少2/5区域)、时间多发(可由 OCB/kFLC 满足)及诊断结论 |
| DMT_decision | 药物选择、筛查项目(乙肝、HIV、VZV、免疫球蛋白、JCV如适用)、生育计划、避孕 |
| follow_up_imaging | 基线后 MRI 的新发/增强病灶,NEDA 评估 |

不要使用 Fazekas 分级。MS 的白质病灶用上面的分区计数描述;Fazekas 是给小血管性白质高信号设计的,只在鉴别诊断中作为对照提及。

## 模块 C3: 帕金森(类型 C)

| 字段 | 说明 |
|---|---|
| cardinal_signs | 运动迟缓(侧别、decrement)、静止性震颤(侧别、频率)、强直、姿势反射 |
| MDS_UPDRS_III | 带日期,区分 ON / OFF(锚定) |
| Hoehn_and_Yahr | 带日期 |
| MDS_criteria_classification | clinically established / probable;列出 supportive criteria、absolute exclusion、red flags |
| levodopa_response | 急性试验或持续用药的改善比例 |
| non_motor | 嗅觉(UPSIT等)、RBD、便秘、体位性血压(卧立位数值)、MoCA、PHQ-9、冲动控制筛查 |
| imaging | MRI 的目的是排除模拟疾病(中脑萎缩、壳核裂隙、十字征、血管性病变);DAT-SPECT 描述不对称性壳核摄取降低 |
| medication_regimen | 每种药的时间点、每次剂量、LEDD(锚定,必须能由药物表算出) |
| motor_complications | wearing-off、异动症、冻结步态 |
| differential_excluded | 特发性震颤、药物性帕金森、血管性帕金森、MSA、PSP、DLB、NPH,每项附依据 |
| lifestyle_and_rehab | 运动、LSVT、职业与日常功能 |
| no_lesion_size | 该病种无 lesion_size 字段(真实病例中为0%) |

可程序化检查: LEDD 总和、用药时间点与次数、MDS-UPDRS 分数随时间的变化与用药情况是否自洽、体位性低血压阈值(收缩压下降≥20 或舒张压≥10)。

---

## 待你核对的清单

- [ ] 卒中: 静脉溶栓、血管内治疗时间窗与流程描述,抗凝开始时机(依梗死体积)
- [ ] MS: 各分区病灶计数与 2024 McDonald 空间多发的对应关系;中央静脉征、顺磁边缘病灶的影像描述习惯
- [ ] MS: 药物(ofatumumab 等)在加拿大的用法与筛查项目
- [ ] 帕金森: LEDD 换算系数(左旋多巴、MAO-B 抑制剂、多巴胺激动剂、COMT 抑制剂)
- [ ] 三个病种的加拿大社会史细节(驾驶规定、药物覆盖、工作场所)

## 后续第二轮

- AD: 真实样本只有9条(其中一条实为路易体痴呆),模块需要用最新诊断标准(含生物标志物)补足后再写。
