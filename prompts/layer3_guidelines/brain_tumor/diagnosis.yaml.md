# Layer 3 — Guidance: brain_tumor/diagnosis.yaml (先用Markdown起草,确认后再转纯yaml)

- 日期: 2026-09-30
- 用途: 约束 layer2/brain_tumor.md 里 molecular_markers、histopathology 字段的具体数值
- 状态: 部分已查证(WHO CNS5分子诊断标准),部分待核对(放射报告描述习惯)

---

```yaml
- id: bt-dx-001
  source: "WHO Classification of Tumours of the Central Nervous System, 5th edition (WHO CNS5), 2021"
  version: "5th edition (2021)"
  domain: ["molecular_markers", "histopathology"]
  strength: mandatory
  rule: >
    自WHO CNS5起,星形细胞瘤的诊断以分子特征为核心,不再单纯依赖组织学形态。IDH野生型弥漫性
    星形细胞瘤,若同时具备以下三项分子特征中任意一项,即可诊断为"Glioblastoma, IDH-wildtype,
    CNS WHO grade 4"(分子胶质母细胞瘤),即使组织学上尚未见到典型的坏死或微血管增生:
    (1) TERT启动子突变; (2) EGFR基因扩增; (3) 7号染色体获得联合10号染色体缺失(+7/-10)。
    这三项里只要满足一项即可下分子诊断,不需要三项同时满足。生成文档中如果已经写了坏死/
    微血管增生等组织学高级别特征,仍应补充分子检测结果以体现当前诊断标准,不能只靠组织学
    形态下grade 4诊断而略去分子检测。
  exceptions: []

- id: bt-dx-002
  source: "WHO CNS5 (2021); CDKN2A/B homozygous deletion as grading criterion"
  version: "5th edition (2021)"
  domain: ["molecular_markers", "histopathology"]
  strength: recommended
  rule: >
    对IDH突变型星形细胞瘤,CDKN2A/B纯合缺失(homozygous deletion)是判定为CNS WHO grade 4
    的独立分子标准,即使组织学分级看起来较低。生成IDH突变型胶质瘤病例、且希望体现grade 4
    行为时,molecular_markers字段应考虑纳入CDKN2A/B缺失状态这一项(此前的demo v2.1里
    molecular_markers只列了IDH/MGMT/1p19q/TERT/EGFR/+7-10/H3K27M/BRAF,未纳入CDKN2A/B,
    建议在该病种生成时按需补充)。
  exceptions:
    - "若病例本身是IDH野生型(经由hd-dx-001其他标准已确诊grade 4),可不强制要求CDKN2A/B数据。"

- id: bt-dx-003
  source: "WHO CNS5 (2021); general principle"
  version: "5th edition (2021)"
  domain: ["molecular_markers"]
  strength: mandatory
  rule: >
    1p/19q共缺失是少突胶质细胞瘤(oligodendroglioma)的必要诊断标准之一(需同时伴IDH突变)。
    生成的病例若分子检测显示1p/19q共缺失阳性,最终诊断应考虑少突胶质细胞瘤而非星形细胞瘤/
    胶质母细胞瘤;若诊断是胶质母细胞瘤,1p/19q应为"not co-deleted"(未共缺失),不能同时
    写"胶质母细胞瘤"又写"1p/19q共缺失阳性",这是自相矛盾的分子特征组合。
  exceptions: []
```

## 待核对清单

- [ ] CDKN2A/B检测方法(FISH/NGS/甲基化芯片)在生成报告里该如何措辞,目前未核实标准表述
- [ ] 脑膜瘤(meningioma)的WHO CNS5分级标准(1-3级)及其分子标记(如TERT启动子突变、CDKN2A/B缺失用于提示脑膜瘤侵袭性),目前layer2/brain_tumor.md的molecular_markers主要针对弥漫性胶质瘤,未覆盖脑膜瘤特异的分级标志物——这批240条真实病例里脑膜瘤和脑肿瘤合并统计,实际分子标记需求可能不同,下次统计时建议拆开看
