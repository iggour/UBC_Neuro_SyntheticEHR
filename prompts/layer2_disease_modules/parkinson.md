# Layer 2 — Disease Module: 帕金森病(退行性,以临床诊断为主)

- 日期: 2026-09-29(从 canonical_facts_template_v1_modules_stroke_ms_pd.md 拆分)
- 类型: C 退行性/以临床诊断为主
- 配套: `layer1_general_template.md`(通用层)、`layer3_guidelines/parkinson.md`(待建)
- 参考标准: MDS 帕金森病临床诊断标准(2015)

| 字段 | 说明 |
|---|---|
| cardinal_signs | 运动迟缓(侧别、decrement)、静止性震颤(侧别、频率)、强直、姿势反射 |
| MDS_UPDRS_III | 带日期,区分 ON / OFF(锚定) |
| Hoehn_and_Yahr | 带日期 |
| MDS_criteria_classification | clinically established / probable;列出 supportive criteria、absolute exclusion、red flags |
| levodopa_response | 急性试验或持续用药的改善比例 |
| non_motor | 嗅觉(UPSIT等)、RBD、便秘、体位性血压(卧立位数值)、MoCA、PHQ-9、冲动控制筛查 |
| imaging | MRI 的目的是排除模拟疾病(中脑萎缩、壳核裂隙、十字征、血管性病变);DAT-SPECT 描述不对称性壳核摄取降低 |
| medication_regimen | 每种药的时间点、每次剂量、LEDD(锚定,必须能由药物表算出) |
| motor_complications | wearing-off、异动症、冻结步态 |
| differential_excluded | 特发性震颤、药物性帕金森、血管性帕金森、MSA、PSP、DLB、NPH,每项附依据 |
| lifestyle_and_rehab | 运动、LSVT、职业与日常功能 |
| no_lesion_size | 该病种无 lesion_size 字段(真实病例中为0%) |

## 可程序化检查

- LEDD 总和(须能从药物列表逐项算出)
- 用药时间点与次数
- MDS-UPDRS 分数随时间的变化与用药情况是否自洽
- 体位性低血压阈值(收缩压下降≥20 或舒张压≥10)
- DAT-SPECT侧别与临床症状侧别为对侧关系(不对称摄取降低侧 vs 症状较重侧相反)

## 待核对清单

- [ ] LEDD 换算系数(左旋多巴、MAO-B 抑制剂、多巴胺激动剂、COMT 抑制剂各自的系数)——目前demo中只用了levodopa 1:1和MAO-B抑制剂固定100的简化算法,未系统核实换算表
