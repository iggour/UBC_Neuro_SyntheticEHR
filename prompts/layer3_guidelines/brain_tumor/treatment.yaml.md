# Layer 3 — Guidance: brain_tumor/treatment.yaml (先用Markdown起草,确认后再转纯yaml)

- 日期: 2026-09-30
- 用途: 约束 layer2/brain_tumor.md 里放化疗方案相关字段(目前该字段隐含在Facts Sheet的
  treatment.disease_modifying里,layer2本身没有单独列"治疗方案"字段,这是一个待补的缺口,
  见下方待核对清单)
- 状态: 已查证(多个来源交叉确认,含Radiopaedia综述、加拿大/爱尔兰癌症用药方案文件、原始Stupp 2005研究引用)

---

```yaml
- id: bt-tx-001
  source: "Stupp et al. 2005 (original trial); cross-checked against Cancer Care Ontario temozolomide monograph and HSE Ireland NCCP chemotherapy regimen, retrieved 2026-09-30"
  version: "Stupp protocol, standard of care since 2005; dosing details per current provincial/institutional formularies"
  domain: ["treatment", "disease_modifying"]
  strength: mandatory
  rule: >
    新诊断胶质母细胞瘤的标准放化疗方案(Stupp方案): 放疗总剂量60Gy,每日2Gy,每周5次(周一
    至周五),共6周;同步期替莫唑胺75mg/m²,每日一次,持续放疗全程(约42天,7天/周服药,
    不是只在放疗日服药);放疗结束后4周左右开始辅助期,替莫唑胺150-200mg/m²,每日一次,
    每28天周期的第1-5天服药,共6个周期。第1周期从150mg/m²起始,若第1周期无明显血液学毒性,
    第2周期起可升至200mg/m²,维持该剂量至第6周期;若出现毒性则维持150mg/m²不升级。
    生成文档中,"同步放化疗"阶段的剂量不能写成150-200mg/m²(那是辅助期剂量),必须是75mg/m²;
    两个阶段剂量不能混淆。
  exceptions:
    - "部分方案(如老年/体能状态较差患者)可能采用更保守的放疗分割方式或单纯化疗,需在病例中
       明确说明理由(如年龄>70岁、KPS较低),不能无理由地偏离标准Stupp方案。"

- id: bt-tx-002
  source: "Cancer Care Ontario temozolomide monograph; HSE Ireland NCCP regimen; drug product monograph (SmPC), retrieved 2026-09-30"
  version: "同上"
  domain: ["safety_and_screening", "monitoring_requirements"]
  strength: mandatory
  rule: >
    替莫唑胺同步放化疗期间(75mg/m²),肺孢子菌肺炎(PJP/PCP)预防性用药是必须的,不是可选项
    (多个来源明确指出"因淋巴细胞减少风险,所有接受同步放化疗的患者都需要PJP预防")。辅助期
    (150-200mg/m²单周期用药)则按淋巴细胞减少程度分级决定是否需要预防性用药: 剂量>75mg/m²
    或者≤75mg/m²但合并放疗时为中度风险,建议常规预防;单纯≤75mg/m²不合并放疗时为低度风险,
    通常不需要常规预防,按需(PRN)处理。生成文档中,若病例进入同步放化疗阶段,必须提及PJP
    预防用药(如trimethoprim-sulfamethoxazole),不能省略这一项。
  exceptions: []

- id: bt-tx-003
  source: "Cancer Care Ontario temozolomide monograph; general principle"
  version: "同上"
  domain: ["medications", "monitoring_requirements"]
  strength: mandatory
  rule: >
    同步放化疗期间,血常规(CBC)监测频率为基线后每周一次。辅助期监测为每周期第1天和第22天
    (或按机构方案)。生成文档如果提到"每月复查血常规"这类描述用于同步放化疗阶段,是频率
    过低的错误,应为每周一次。
  exceptions: []
```

## 待核对清单

- [ ] layer2/brain_tumor.md目前没有单独的"treatment_regimen"字段来承载这些放化疗方案细节,
      建议下次修订layer2时补充这个字段,明确区分"同步期"和"辅助期"两个阶段各自的剂量、
      监测要求,而不是只靠Facts Sheet里的treatment.disease_modifying这一个自由文本字段承载
- [ ] 老年/体能状态较差患者的替代方案(如单纯短程放疗、单纯化疗)具体剂量调整,本次未查证
- [ ] 贝伐珠单抗(bevacizumab)等二线/复发治疗方案剂量,本次未查证(demo v2.1里brain_tumor的
      medications_prescribed高频里出现过bevacizumab,但layer3还没有对应的剂量验证)
