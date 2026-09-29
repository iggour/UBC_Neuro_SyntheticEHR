# Layer 2 — Disease Module: 卒中(急性血管性局灶病变)

- 日期: 2026-09-29(从 canonical_facts_template_v1_modules_stroke_ms_pd.md 拆分)
- 类型: A 局灶结构病变
- 配套: `layer1_general_template.md`(通用层)、`layer3_guidelines/stroke.md`(待建)
- 参考标准: 加拿大卒中最佳实践指南(2022更新,替奈普酶 0.25 mg/kg,最大25 mg)

| 字段 | 说明 |
|---|---|
| time_last_known_well / symptom_onset / arrival | 精确到分钟,锚定;所有时间指标由它们推出 |
| NIHSS_at_arrival / 24h / discharge / follow-up | 带日期的量表分数(锚定) |
| vascular_territory | 如 左MCA M1;必须与症状侧别、失语/偏瘫类型一致(注意:病灶与偏瘫为对侧关系) |
| imaging_acute | CT: ASPECTS、致密动脉征、出血;CTA: 闭塞部位、颈动脉狭窄、侧支;CTP: 核心梗死体积、Tmax>6s 体积、不匹配比 |
| reperfusion_treatment | 静脉溶栓(药物、剂量按体重计算、给药时间)、血管内治疗(方法、mTICI、穿刺/再通时间) |
| door_to_needle / door_to_puncture | 由时间点自动计算,不得与时间线冲突 |
| infarct_MRI | DWI 梗死部位与体积,是否出血转化 |
| etiology_TOAST | 大动脉粥样硬化 / 心源性栓塞 / 小血管 / 其他 / 不明 |
| etiologic_workup | ECG/监测、超声心动图(LVEF、左房、血栓、PFO)、颈动脉/血管影像、血脂、HbA1c |
| secondary_prevention | 抗栓/抗凝药物(含开始日期及启动时机的理由——依据梗死体积与出血转化风险权衡)、他汀及 LDL 目标、血压目标 |
| outcome_90d | mRS、NIHSS、残留缺损(失语类型等) |
| rehabilitation_and_return | 康复、语言治疗、驾驶、工作、抑郁筛查 |

## 已核对并修正的问题

- **抗凝启动时机缺乏理由**: demo v1只写了"day 5开始抗凝",未说明为什么不是day 1或day 14。已修正为明确写出:依据梗死体积(22mL)与出血转化风险的权衡,day 5前复查CT排除间隔出血后再启动。

## 可程序化检查

- 时间线单调递增、door-to-needle/door-to-puncture 计算
- 偏瘫侧别与病灶侧别相反(对侧关系)
- 溶栓给药剂量 = 体重 × 0.25(上限25 mg)

## 真实分布软约束

起病模式94%记录为急性;量表出现率68%;遗传相关信息仅6%,主要来自线粒体病等特殊病因亚型。生成时可按"典型心源性栓塞/大动脉粥样硬化/罕见病因"设置病因亚型种子。

## 待核对清单

- [ ] 血管内治疗时间窗与流程描述是否符合最新加拿大指南
- [ ] 抗凝开始时机(依梗死体积分层)的具体天数是否有更精确的循证依据
