# Layer 3 — Guidance: huntington/diagnosis.yaml (先用Markdown起草,确认后再转纯yaml)

- 日期: 2026-09-29
- 用途: 约束layer2/huntington.md里 genetic_confirmation、cag_interpretation_reference、UHDRS 字段的具体数值
- 状态: 起草,已查证部分标注verified,未查证部分标注pending

---

```yaml
- id: hd-dx-001
  source: "American College of Medical Genetics/American Society of Human Genetics HD Genetic Testing Working Group (1998); consistent with Mayo Clinic Labs, PanelApp (ClinGen), ARUP Labs reference ranges (cross-checked 2026-09-29)"
  version: "n/a (long-established, stable reference range)"
  domain: ["genetic_confirmation", "cag_interpretation_reference"]
  strength: mandatory
  rule: >
    HTT CAG重复数解读: ≤26重复 = 正常; 27-35重复 = 中间型(不发病,但传递给后代时可能扩增,
    对本人无风险); 36-39重复 = 不完全外显(有发病风险,但不必然发病); ≥40重复 = 完全外显
    (随正常寿命几乎必然发病)。生成文档时,任何"确诊"表述必须对应≥40重复的等位基因;
    36-39重复的病例不应写成"确诊",应写"不完全外显,有患病风险"。
  exceptions: []

- id: hd-dx-002
  source: "general genetic counseling practice for autosomal dominant conditions"
  version: "n/a"
  domain: ["differential", "family_history_structured"]
  strength: recommended
  rule: >
    亨廷顿病是常染色体显性遗传,患者每个子女有50%概率遗传致病等位基因。生成的鉴别诊断/
    家族史讨论中,涉及子女或亲属的遗传咨询建议时,应体现: (1) 未成年子女不应进行预测性
    基因检测; (2) 症状前成年亲属的预测性检测需要正式遗传咨询,不是常规检验项目。
  exceptions: []

- id: hd-dx-003
  source: "UHDRS (Unified Huntington's Disease Rating Scale), Huntington Study Group, 1996"
  version: "UHDRS-99 (标准版本)"
  domain: ["severity_scores"]
  strength: mandatory
  rule: >
    UHDRS包含四个独立子部分: Motor(运动评分,总分0-124,分数越高越重)、Cognitive(认知,
    含语言流畅性/符号数字模式测验/Stroop等子测验)、Behavioral(行为)、Functional
    (含Total Functional Capacity总分0-13、Functional Assessment总分0-25、Independence
    Scale)。这四部分互相独立评分,不能合并成一个"UHDRS总分"。PBA-s(Problem Behaviours
    Assessment short form)是独立于UHDRS的另一个工具,不属于UHDRS的Behavioral子部分,
    两者不能混淆或互相替代。
  exceptions: []
  note_pending: "UHDRS Cognitive子部分的具体测验清单(哪几个测验、各占多少分)尚未逐条核实,标记pending,暂不在生成文档中要求列出Cognitive子部分的具体分数,只用独立的MoCA/SDMT等作为认知筛查。"
```
