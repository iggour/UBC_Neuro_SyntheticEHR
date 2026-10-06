# Layer 3 — Guidance: ms/treatment.yaml (先用Markdown起草,确认后再转纯yaml)

- 日期: 2026-09-30
- 用途: 约束 layer2/ms.md 里 DMT_decision 字段(疾病修饰治疗的筛查/安全要求)
- 状态: 部分已查证(通用原则层面),具体药物的筛查清单细节本次未逐一深入核实,按"待核对"处理

---

```yaml
- id: ms-tx-001
  source: "general principle for anti-CD20 therapies (ofatumumab, ocrelizumab) and natalizumab in MS"
  version: "n/a (通用原则,具体药物细节待核对)"
  domain: ["DMT_decision", "safety_and_screening"]
  strength: mandatory
  rule: >
    启动抗CD20药物(ofatumumab、ocrelizumab)前,必须完成乙型肝炎(HBsAg、HBcAb)筛查、
    免疫球蛋白水平检测,并确认水痘带状疱疹免疫状态(既往感染或疫苗接种史)。启动natalizumab
    前,必须检测JC病毒抗体(用于评估进行性多灶性白质脑病PML风险)。生成文档中,若病例选择
    了这类药物作为DMT,必须体现对应的筛查步骤已完成,不能跳过直接开始用药。
  exceptions: []

- id: ms-tx-002
  source: "general principle for MS DMT and pregnancy planning"
  version: "n/a"
  domain: ["DMT_decision", "pregnancy"]
  strength: recommended
  rule: >
    育龄期女性患者启动DMT前,应讨论妊娠计划及避孕方式,部分DMT在妊娠期使用的安全性数据
    有限,需要在用药决策讨论中体现这一层考虑,不能完全忽略生育计划这个变量。
  exceptions: []
```

## 待核对清单

- [ ] ofatumumab/ocrelizumab/natalizumab各自具体的筛查项目清单(本次只给出了通用原则,
      没有逐一列出每种药物的完整筛查checklist,比如natalizumab的JCV抗体具体阈值分层
      和对应的PML风险评估流程)
- [ ] 不同DMT在妊娠期/哺乳期的具体安全性分级(本次只提到"需要讨论",没有给出具体的
      药物分级建议)
- [ ] 疫苗接种时机与DMT启动的先后顺序(比如水痘疫苗如需补种,应在哪类DMT启动前完成),
      本次未核实
