# Layer 3 — Guidance: parkinson/diagnosis.yaml (先用Markdown起草,确认后再转纯yaml)

- 日期: 2026-09-30
- 用途: 约束 layer2/parkinson.md 里 MDS_criteria_classification 字段
- 状态: 基本结构已核实,具体红旗症状/支持性标准的完整清单本次未逐条重新核对原始文献

---

```yaml
- id: pd-dx-001
  source: "MDS Clinical Diagnostic Criteria for Parkinson's Disease, Postuma et al. 2015,
           Movement Disorders"
  version: "2015"
  domain: ["MDS_criteria_classification", "cardinal_signs"]
  strength: mandatory
  rule: >
    MDS 2015标准要求核心运动症状为: 运动迟缓(必须存在)+ 静止性震颤和/或强直(至少一项)。
    诊断分两级: "临床确诊(clinically established)"需满足核心运动症状+无绝对排除标准+
    至少2项支持性标准+无红旗症状;"临床可能(clinically probable)"允许存在红旗症状,
    但必须有相应数量的支持性标准来抵消。生成文档中,若病例标注为"clinically established",
    必须在鉴别诊断部分体现"无红旗症状"这一条,不能只罗列支持性标准而不提红旗症状的
    排除情况。
  exceptions: []

- id: pd-dx-002
  source: "MDS 2015 criteria, general structure"
  version: "2015"
  domain: ["differential_excluded"]
  strength: recommended
  rule: >
    常见红旗症状包括(不限于): 发病5年内出现轮椅依赖的快速进展、完全无运动症状进展、
    早期球部功能障碍、发病5年内出现吸入性呼吸功能障碍、早期严重自主神经功能障碍、
    发病3年内反复跌倒、不成比例的颈部前屈或手足挛缩、发病5年内无常见非运动症状、
    其他不能解释的锥体束征、双侧对称的帕金森症状。生成"clinically established"病例时,
    应在病史/查体部分明确体现这些红旗症状均未出现,而不是完全不提及这个判断维度。
  exceptions: []
```

## 待核对清单

- [ ] 支持性标准(supportive criteria)的完整清单本次未逐条核对(目前layer2/demo中只用了
      "静止性震颤+嗅觉减退+levodopa反应"三项,MDS标准原文可能有更多项,如病程中出现的
      左旋多巴诱发的异动症、嗅觉检测客观异常等,需要补全)
- [ ] 绝对排除标准(absolute exclusion criteria)的完整清单本次完全未核对(目前demo中
      只写了"无绝对排除标准",没有列出具体是哪些,比如小脑性体征、核上性垂直凝视麻痹、
      明确的额颞叶痴呆诊断等)
