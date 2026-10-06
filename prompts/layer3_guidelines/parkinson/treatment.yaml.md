# Layer 3 — Guidance: parkinson/treatment.yaml (先用Markdown起草,确认后再转纯yaml)

- 日期: 2026-09-30
- 用途: 约束 layer2/parkinson.md 里 medication_regimen 字段的 LEDD 计算
- 状态: 已查证(Tomlinson et al. 2010,多个独立临床试验统计分析计划文件交叉确认一致),
  这是之前明确标记为"待核对"的缺口,本次已补全

---

```yaml
- id: pd-tx-001
  source: "Tomlinson et al. 2010, Movement Disorders (原始系统综述); 交叉核对多份临床试验
           统计分析计划(SAP)文件中实际采用的换算系数,retrieved 2026-09-30"
  version: "Tomlinson 2010原版(后续有学者提出opicapone/safinamide等新药的补充换算系数,
           本次未涉及这两种药物,暂不需要)"
  domain: ["medication_regimen", "LEDD"]
  strength: mandatory
  rule: >
    LEDD(左旋多巴等效日剂量)换算系数表(以mg为单位计算):
      - 左旋多巴(标准/速释): 剂量 × 1
      - 左旋多巴控释剂型(CR): 剂量 × 0.75
      - 左旋多巴缓释剂型(ER,如Rytary): 剂量 × 0.5
      - 恩他卡朋(entacapone)/与左旋多巴联用: 联用的左旋多巴剂量 × 0.33(不是恩他卡朋
        本身的剂量乘以系数,是让左旋多巴剂量本身按比例增加)
      - 普拉克索(pramipexole,速释/缓释): 剂量 × 100
      - 罗匹尼罗(ropinirole): 剂量 × 20
      - 罗替戈汀(rotigotine): 剂量 × 30
      - 司来吉兰(selegiline)口服: 剂量 × 10;舌下: 剂量 × 80
      - 雷沙吉兰(rasagiline): 剂量 × 100(之前demo v2.1里用的"rasagiline 1mg = LEDD 100"
        这个换算是对的,与此表一致,无需修改)
      - 金刚烷胺(amantadine): 剂量 × 1
      - 阿扑吗啡(apomorphine,持续输注): 全天总剂量 × 10
    生成文档中计算LEDD总和时,必须按此表逐项换算后相加,不能凭印象估算或跳过某一类药物
    的换算系数。此前demo v2.1中只用了levodopa按1:1、rasagiline固定加100这种简化算法,
    这是对的(因为那份demo恰好只涉及这两种药),但如果后续生成涉及普拉克索、罗匹尼罗等
    其他药物的病例,必须按上表对应系数计算,不能继续套用"levodopa 1:1"这种简化模式。
  exceptions:
    - "恩他卡朋的换算规则是特例:不是把恩他卡朋本身的mg数乘以系数相加,而是让同服的左旋
       多巴剂量乘以0.33后,作为'恩他卡朋贡献的LEDD'单独一项加总,不要把这一步和左旋多巎
       本身的LEDD计算搞混(即左旋多巴本身仍按×1计算一份,恩他卡朋带来的额外LEDD按
       左旋多巴剂量×0.33再加一份,两者相加)。"
```

## 待核对清单

- [ ] opicapone、safinamide这两种较新药物的换算系数(Tomlinson原表没有,后续学者提出了
      补充系数,本次未纳入,若后续病例用到这两种药需要另外核实)
- [ ] 麦角类多巴胺激动剂(如pergolide、cabergoline、bromocriptine)的换算系数本次查到了
      数字(pergolide×100、cabergoline×100、bromocriptine×10)但未深入核实来源一致性,
      建议谨慎使用,优先用非麦角类药物
