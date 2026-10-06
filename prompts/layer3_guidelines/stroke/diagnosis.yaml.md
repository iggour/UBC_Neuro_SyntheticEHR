# Layer 3 — Guidance: stroke/diagnosis.yaml (先用Markdown起草,确认后再转纯yaml)

- 日期: 2026-09-30
- 用途: 约束 layer2/stroke.md 里 reperfusion_treatment、NIHSS、imaging_acute 相关字段
- 状态: 已查证(溶栓剂量此前已核实;本次新核实TOAST分型的影像排除逻辑)

---

```yaml
- id: str-dx-001
  source: "tenecteplase product monograph; Canadian Stroke Best Practice Recommendations 2022 update"
  version: "2022 update"
  domain: ["reperfusion_treatment"]
  strength: mandatory
  rule: >
    替奈普酶(tenecteplase)静脉溶栓标准剂量为0.25mg/kg,单次静脉推注,最大剂量不超过25mg。
    不是按体重连续给药,是一次性推注。生成文档中剂量计算必须能用"体重×0.25"精确对应,
    且不超过25mg上限(即体重超过100kg的患者仍按25mg给,不按比例继续增加)。
  exceptions: []

- id: str-dx-002
  source: "general principle of TOAST classification; standard stroke workup"
  version: "n/a"
  domain: ["etiology_TOAST", "etiologic_workup"]
  strength: mandatory
  rule: >
    诊断为"心源性栓塞(cardioembolism)"病因,必须在workup中排除大动脉粥样硬化(颈动脉/
    颅内血管狭窄<50%或影像未见明显狭窄)和小血管病(梗死范围不是典型的腔隙性小梗死模式)。
    若CTA/MRA显示明显血管狭窄(≥50%),应考虑大动脉粥样硬化机制,不应直接归为心源性栓塞,
    需要在鉴别诊断部分明确讨论两种机制如何区分,不能只因为发现房颤就默认是心源性,
    忽略同时存在的血管狭窄证据。
  exceptions:
    - "若患者同时具备房颤和显著血管狭窄,TOAST分型应为'多种可能病因(unclassified/multiple)'
       而非单一归类为心源性栓塞,这种情况需要明确说明。"
```

## 待核对清单

- [ ] ASPECTS评分的具体扣分区域标准(本次未逐条核实10个评分区域的具体解剖对应关系)
- [ ] 血管内治疗的时间窗口(发病后多少小时内可以治疗)本次未查证最新标准
