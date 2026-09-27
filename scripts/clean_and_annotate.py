import json
import os

disease_files = ["stroke", "multiple_sclerosis", "parkinson", "alzheimer", "huntington", "brain_tumor"]

# 用来做模态完整度检测的简单关键词代理(先用规则粗筛,后面再考虑要不要上LLM精筛)
modality_keywords = {
    "has_imaging": ["mri", "ct scan", "ct imaging", "imaging showed", "imaging revealed",
                     "t1", "t2", "flair", "contrast-enhanced", "radiograph"],
    "has_labs": ["laboratory", "blood test", "csf analysis", "cerebrospinal fluid",
                 "白细胞", "wbc", "hemoglobin", "creatinine", "glucose level"],
    "has_medication": ["mg/day", "mg twice daily", "was started on", "treated with",
                        "prescribed", "dosage", "medication"],
    "has_followup": ["follow-up", "follow up", "months later", "years later",
                      "at 6-month", "at 1-year", "on subsequent visit", "readmitted"]
}

def looks_like_review_not_case(case_text, age):
    """粗筛:age为null 且 文本看起来不像单一患者叙事"""
    if age is not None:
        return False
    review_signals = ["we reviewed", "this review", "meta-analysis", "systematic review",
                       "we summarize", "the literature", "case series of"]
    text_lower = case_text.lower()
    return any(sig in text_lower for sig in review_signals)

for disease in disease_files:
    filepath = f"data/by_disease/{disease}_cases.json"
    if not os.path.exists(filepath):
        continue
    with open(filepath, encoding="utf-8") as f:
        cases = json.load(f)

    annotated = []
    removed_reviews = 0

    for case in cases:
        text = case["case_text"]
        age = case["age"]

        if looks_like_review_not_case(text, age):
            removed_reviews += 1
            continue

        text_lower = text.lower()
        modality_flags = {
            key: any(kw in text_lower for kw in kws)
            for key, kws in modality_keywords.items()
        }

        case["modality_completeness"] = modality_flags
        case["completeness_score"] = sum(modality_flags.values())  # 0-4分,越高越完整
        annotated.append(case)

    with open(f"data/by_disease/{disease}_cases_annotated.json", "w", encoding="utf-8") as f:
        json.dump(annotated, f, ensure_ascii=False, indent=2)

    print(f"{disease}: 原始{len(cases)}条 -> 剔除疑似综述{removed_reviews}条 -> 保留{len(annotated)}条")
    avg_score = sum(c["completeness_score"] for c in annotated) / len(annotated) if annotated else 0
    print(f"  平均完整度分数: {avg_score:.2f}/4\n")
