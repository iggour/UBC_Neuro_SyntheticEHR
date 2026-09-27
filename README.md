# UBC Neuro Synthetic EHR Project

## 项目目标
从MultiCaRe公开病例报告数据集中提取神经科病例,分析真实病例的canonical facts结构规律,
用于设计"合成神经科病历生成系统"的分层字段模板,并生成demo病例供导师方向确认。

## 数据来源
- OpenMed/multicare-cases (Hugging Face), 完全公开许可, 来源为PubMed Central已发表病例报告
- 覆盖病种: stroke, multiple_sclerosis, parkinson, alzheimer, huntington, brain_tumor

## 处理流程 (按运行顺序)

1. `scripts/filter_neuro.py`
   从MultiCaRe全量数据流式筛选神经科相关病例(基于关键词,部分词做了位置限制处理"顺带提及"误判)
   输出: data/raw/neuro_cases_raw.json (300条)

2. `scripts/split_by_disease.py`
   按疾病关键词拆分成6个子文件
   输出: data/by_disease/{disease}_cases.json

3. `scripts/clean_and_annotate.py` [已弃用,被第4步的LLM方法取代]
   规则方法剔除疑似综述、粗筛模态完整度,规则方法精度不足

4. `scripts/llm_annotate.py`
   用DeepSeek API逐条判断: 是否为有效单一病例(非综述)、神经疾病是否为主诉相关(非既往史误提)、
   量表/基因检测/起病模式/鉴别诊断/家族史等12个维度
   输出:
   - data/by_disease/{disease}_cases_llm_annotated.json (全量,含无效/非主诉病例,供回溯)
   - data/by_disease/{disease}_cases_valid_primary.json (精筛,仅保留有效且主诉相关)

5. `scripts/extract_canonical_facts.py`
   用DeepSeek API对精筛后的病例提取17个结构化字段(主诉/病灶定位/量表/用药/随访等)
   输出: data/by_disease/{disease}_canonical_facts.json

   已知问题(待正式实验时修复):
   differential_diagnoses_considered 字段有时会把"最终确诊疾病"误算入鉴别诊断列表,
   需要在prompt中明确"不包括最终确诊疾病本身"

6. `scripts/summarize_facts.py`
   汇总统计每个病种各字段的非空率及高频具体值,用于设计分层canonical facts模板

## 数据处理结果摘要(2026年9月)
| 病种 | 原始筛选 | LLM精筛后 |
|---|---|---|
| stroke | 51 | 31 |
| multiple_sclerosis | 67 | 56 |
| parkinson | 30 | 24 |
| alzheimer | 20 | 9 |
| huntington | 6 | 5 |
| brain_tumor | 132 | 115 |
| **合计** | **306** | **240** |

## 关键发现
- lesion_size字段: 帕金森/AD/亨廷顿均为0%非空,结构性病变类(卒中/脑肿瘤/MS)才适用
  → canonical facts需分层设计,不能用统一模板覆盖所有病种
- genetic_testing: 亨廷顿80%非空(确诊性检测) vs 其他病种<25%(偶发辅助检查)
- family_history非空率与遗传成分强弱对应: 卒中3% < 帕金森33% < AD44% < 亨廷顿60%
- 脑肿瘤clinical_scales_used高频为BCVA/视野(视功能),提示病灶位置决定伴随功能评估类型

## 环境配置
- Python 3.12, 依赖: datasets, pandas, openai
- API: DeepSeek (环境变量 DEEPSEEK_API_KEY, 存于 ~/.zshrc)

## 下一步计划
- 修复differential_diagnoses_considered的prompt问题
- 聚焦brain_tumor + huntington两个病种,设计分层字段清单文档
- 生成2份demo病例(体现纵向多文档结构+鉴别诊断层),供导师确认方向
