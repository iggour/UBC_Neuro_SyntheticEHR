# Layer 3 — Guidance: ms/diagnosis.yaml (先用Markdown起草,确认后再转纯yaml)

- 日期: 2026-09-30
- 用途: 约束 layer2/ms.md 里 MRI_lesion_counts_by_region、criteria_statement、CSF 字段
- 状态: 部分已查证(kFLC阈值此前在demo设计时已确认),DIS/DIT具体门槛数值本次未逐条重新核实原始文献,按layer2现有内容标注为"沿用demo v2.1已用口径"

---

```yaml
- id: ms-dx-001
  source: "Multicenter studies (Hegen et al., Frontiers in Immunology 2023; Leurs et al.;
           Monreal et al., Frontiers in Immunology 2023), cross-checked 2026-09-30. Cutoff of
           6.1 is the one adopted into the 2024 McDonald criteria as an OCB alternative."
  version: "2024 McDonald criteria adoption; cutoff validated across multiple independent cohorts (combined >3300 CIS/MS patients)"
  domain: ["CSF"]
  strength: mandatory
  rule: >
    脑脊液kappa游离轻链(kFLC)指数阳性阈值为6.1,已被多个独立大型多中心研究验证
    (敏感性约86-93%,特异性约90-94%,与寡克隆带诊断效能相当),并已纳入2024年McDonald
    标准作为OCB的替代/补充检测。生成文档中引用该数值应保持一致,这是经过验证的标准值,
    不是暂定口径。注意: kFLC指数敏感性略高于OCB,但特异性略低于OCB(尤其在视神经炎患者
    中特异性较低);若两者结果不一致,OCB阳性仍应被视为有效支持证据,不应因kFLC阴性而
    否定OCB阳性的诊断价值。
  exceptions:
    - "肾功能减退患者的血清kFLC水平可能继发性升高,需结合血清/脑脊液比值(如kFLC指数而非
       单纯脑脊液kFLC绝对值)判断,单纯脑脊液kFLC浓度升高不能孤立地当作阳性证据。"

- id: ms-dx-002
  source: "McDonald诊断标准的基本逻辑结构(2017/2024版均遵循此结构);不要求模型自己推导"
  version: "沿用demo v2.1已用的2024年修订版口径"
  domain: ["criteria_statement"]
  strength: mandatory
  rule: >
    空间多发(DIS)需要在5个区域(脑室周围、皮层下/近皮层、幕下、脊髓、视神经)中至少
    2个区域有典型MS病灶;时间多发(DIT)可以由单次MRI上同时存在增强和非增强病灶满足,
    也可以由CSF寡克隆带阳性满足,不要求必须有两次间隔的MRI扫描才能下诊断。生成文档中
    判断DIS/DIT是否满足时,必须按layer1规定的"逐条列出每个区域/每个标准是否满足"的
    方式呈现,不能用一句话笼统下结论。
  exceptions: []

- id: ms-dx-003
  source: "general principle: NMOSD/MOGAD differential requires antibody testing by cell-based assay"
  version: "n/a"
  domain: ["differential_excluded", "serum_antibodies"]
  strength: mandatory
  rule: >
    排除NMOSD必须基于AQP4-IgG检测,排除MOGAD必须基于MOG-IgG检测,且检测方法应明确标注为
    细胞法(cell-based assay)——这是目前敏感性/特异性最好的检测方法,ELISA法假阳性率
    较高。生成文档中若提到这两项抗体检测,应注明检测方法,不能只写"抗体阴性"而不说明
    用的什么方法。
  exceptions: []
```

## 待核对清单

- [ ] kFLC指数>6.1这个阈值的原始文献来源,需要专门核实(目前只是沿用了demo设计时的口径)
- [ ] 2024年McDonald标准相对2017版具体新增了哪些条款(比如中央静脉征、顺磁边缘病灶作为
      "支持性但非必需"证据的具体措辞),本次没有重新深入核对,只核对了基本DIS/DIT结构
- [ ] 不同DMT药物(ofatumumab、ocrelizumab、natalizumab等)各自的筛查清单细节(JCV抗体
      何时需要查、妊娠相关禁忌具体时限),本次未逐一核实
