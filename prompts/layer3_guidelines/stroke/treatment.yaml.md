# Layer 3 — Guidance: stroke/treatment.yaml (先用Markdown起草,确认后再转纯yaml)

- 日期: 2026-09-30
- 用途: 约束 layer2/stroke.md 里 secondary_prevention(抗凝启动时机)字段
- 状态: 已查证,但这是一条"专家共识、非高级别循证依据"的规则,且近年有更早启动的新证据,
  需要在规则里诚实标注这个不确定性,不能当作绝对标准处理

---

```yaml
- id: str-tx-001
  source: "'1-3-6-12 day rule' (Diener's law), originally European Heart Rhythm Association/
           European Society of Cardiology 2013 consensus, adopted by AHA/ASA and European Stroke
           Organisation guidelines; cross-checked against multiple 2024-2025 reviews, retrieved
           2026-09-30"
  version: "传统共识版本(2013起);注意:近年随机对照试验(如TIMING、ELAN、OPTIMAS)及meta分析
           提示更早启动可能同样安全,该领域指南正在演变中,不是稳定不变的标准"
  domain: ["secondary_prevention", "reperfusion_treatment"]
  strength: recommended
  rule: >
    心源性栓塞(房颤相关)缺血性卒中后,口服抗凝药启动时机的经典专家共识("1-3-6-12天法则"):
    TIA后1天、轻度卒中(NIHSS<8)后3天、中度卒中(NIHSS 8-15)后6天、重度卒中(NIHSS>15)
    后12天,且启动前须复查影像排除出血转化。另一套按梗死体积分层的参考(非卒中严重度,
    是直接按影像测量的梗死大小): 无梗死或TIA可立即开始;梗死直径≤1.5cm可在2天内开始;
    1.6-3cm在4-5天开始;≥3cm在7天开始。生成文档中,若选择的抗凝启动日期明显早于或晚于
    上述区间(比如严重卒中在抗凝前第1天就启动,或轻度卒中拖到第20天才启动),必须在
    会诊记录里给出具体理由(如同时合并消化道出血史需要更谨慎,或者临床团队采用了更新的
    早期启动证据),不能无理由地偏离,也不要把这条规则当成绝对真理陈述,应体现"这是风险
    权衡后的团队决策,不是唯一正确答案"这种语气。
  exceptions:
    - "若患者接受了血管内取栓且再通良好、梗死核心很小,部分中心现在倾向更早启动抗凝,
       这种情况需要在文档中说明是基于较新证据的团队决策。"
    - "若患者有活动性出血倾向或近期手术,启动时机应相应延后,且需说明原因。"
```

## 待核对清单

- [ ] 血管内治疗后(尤其再通良好)抗凝启动时机是否有专门的、比上述规则更晚或更早的单独指南(规则里提到"部分中心倾向更早",但具体循证依据本次未深入查证)
- [ ] 加拿大具体的卒中二级预防指南(Canadian Stroke Best Practice Recommendations)里对抗凝启动时机是否有和国际共识不同的本地化建议,本次没有专门核对这一点,只核对了溶栓剂量部分
