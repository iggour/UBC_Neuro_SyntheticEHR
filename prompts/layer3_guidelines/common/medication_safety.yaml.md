# Layer 3 — Guidance: common/medication_safety.yaml (示例,非正式YAML文件,先用Markdown起草确认格式)

- 日期: 2026-09-29
- 用途: 跨病种通用的用药安全规则,不含任何病种特异性剂量
- 状态: 起草阶段,先确认字段结构和粒度是否合适,再正式转成 .yaml 并扩充

---

```yaml
- id: common-med-001
  source: "general prescribing safety principle"
  version: "n/a"
  domain: ["medications", "safety_and_screening"]
  strength: mandatory
  rule: >
    任何药物的起始剂量、滴定方案、最大剂量,必须对照该药物的真实处方信息/说明书,
    不能凭一般印象估算或外推。若说明书未明确给出的细节,标注为需要临床判断,
    不得虚构一个看起来合理的数字。
  exceptions: []

- id: common-med-002
  source: "general prescribing safety principle"
  version: "n/a"
  domain: ["medications"]
  strength: mandatory
  rule: >
    涉及基因型指导用药剂量的药物(如需CYP2D6/CYP2C19等分型),必须在文档中体现
    "是否已完成/是否需要完成基因型检测"这一步,不能跳过直接给出高剂量。
  exceptions:
    - "急诊/危及生命情况下的经验性用药可先给药,后续补测基因型"

- id: common-med-003
  source: "general prescribing safety principle"
  version: "n/a"
  domain: ["safety_and_screening"]
  strength: recommended
  rule: >
    涉及可能影响情绪/精神状态的药物(如抗精神病药、抗癫痫药、部分神经科专科用药),
    应在处方前记录基线抑郁/自杀风险筛查(如PHQ-9、C-SSRS),并说明后续复查安排。
  exceptions: []
```
