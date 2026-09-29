# Layer 3 — Guidance: huntington/treatment.yaml (先用Markdown起草,确认后再转纯yaml)

- 日期: 2026-09-29
- 用途: 约束layer2/huntington.md里 symptomatic_treatment 字段的具体数值
- 状态: 起草,已查证

---

```yaml
- id: hd-tx-001
  source: "FDA prescribing information, tetrabenazine tablets (cross-checked against multiple label sources including Apotex/Lupin generic labeling, 2018 revision, retrieved 2026-09-28)"
  version: "2018年修订版说明书(需在正式使用前确认是否有更新版本)"
  domain: ["symptomatic_treatment", "medications"]
  strength: mandatory
  rule: >
    四苯喃嗪(tetrabenazine)治疗HD相关舞蹈症的起始与滴定方案(总剂量≤50mg/day时):
    第1周: 12.5mg/day,晨服一次。
    第2周: 增至25mg/day,分两次(12.5mg,一天两次)。
    第2周之后: 每周递增12.5mg/day,直到达到控制舞蹈症状且能耐受的剂量。
    当日总剂量达到37.5-50mg/day时,须分三次给药,单次最大剂量不超过25mg。
    若患者需要的日剂量超过50mg/day,处方前必须先做CYP2D6基因型检测,区分是
    poor metabolizer(PM,日最大剂量50mg,单次最大25mg)还是extensive/intermediate
    metabolizer(EM/IM,日最大剂量100mg,单次最大37.5mg)。
    生成文档中,任何"起始就给25mg以上"或者"跳过分次给药直接单次给50mg"的方案都是错误的,
    必须体现上述递增节奏。
  exceptions:
    - "严重不良反应(如急性抑郁加重、静坐不能)出现时,应停止递增或减量,不强制按周递增节奏继续加量。"

- id: hd-tx-002
  source: "FDA prescribing information, tetrabenazine tablets (boxed warning section)"
  version: "同上"
  domain: ["safety_and_screening", "monitoring_requirements"]
  strength: mandatory
  rule: >
    四苯喃嗪带有关于抑郁/自杀意念加重的警示。处方前必须记录基线抑郁/自杀风险筛查
    (如PHQ-9、C-SSRS),治疗期间每次随访重复筛查。若患者近期有活动性抑郁或自杀意念,
    需谨慎评估是否适合启动此药,而非常规直接启动。
  exceptions: []

- id: hd-tx-003
  source: "general principle for autosomal dominant late-onset conditions; no single named act should be cited"
  version: "n/a"
  domain: ["safety_and_screening", "social"]
  strength: mandatory
  rule: >
    讨论基因检测结果对保险/就业/家庭的影响时,不点名引用某国具体法律名称(不同司法辖区
    保护范围不同,且随时间修订),用通用表述"存在相关法律保护但有限制,具体细节由遗传
    咨询师/社工在专门环节说明",除非使用者明确提供了准确、现行、适用于该虚拟病例所在
    司法辖区的具体法规引用。
  exceptions:
    - "使用者明确要求并提供了准确的当地现行法规引用时,可以具体引用。"
```
