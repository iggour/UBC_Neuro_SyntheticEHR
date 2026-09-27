from datasets import load_dataset
import json

print("正在加载数据集(流式,不会一次性下载全部)...")
ds = load_dataset("OpenMed/multicare-cases", streaming=True)

# 这些词容易在非神经科病例里被"顺带提及"(既往史/排除诊断/并发症),需要限制只在文本前段出现才算命中
position_sensitive_keywords = [
    "stroke",
    "cerebral infarct", "cerebral ischemi", "brain infarct",
    "intracerebral hemorrhage", "cerebral hemorrhage", "subarachnoid hemorrhage",
]

# 这些词专有名词性质强,极少被顺带提及,不限制位置
specific_keywords = [
    "multiple sclerosis", "demyelinat",
    "parkinson's disease", "parkinsonism",
    "alzheimer",
    "huntington's disease", "huntington disease",
    "brain tumor", "brain tumour", "glioma", "glioblastoma", "meningioma", "astrocytoma"
]

EARLY_LIMIT = 200  # 只在文本前200字内查找position_sensitive_keywords

results = []
count_checked = 0

for row in ds["train"]:
    count_checked += 1
    for case in row["cases"]:
        text = case.get("case_text", "").lower()
        early_text = text[:EARLY_LIMIT]

        matched = []
        for kw in position_sensitive_keywords:
            if kw in early_text:
                matched.append(kw)
        for kw in specific_keywords:
            if kw in text:
                matched.append(kw)

        if matched:
            results.append({
                "article_id": row["article_id"],
                "case_id": case.get("case_id"),
                "age": case.get("age"),
                "matched_keywords": matched,
                "case_text": case.get("case_text")
            })
    if len(results) >= 300:
        break
    if count_checked % 5000 == 0:
        print(f"已检查 {count_checked} 篇文章,已找到 {len(results)} 条相关病例...")

print(f"完成!共筛选出 {len(results)} 条神经科相关病例。")

with open("neuro_cases_raw.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("已保存到 neuro_cases_raw.json")
