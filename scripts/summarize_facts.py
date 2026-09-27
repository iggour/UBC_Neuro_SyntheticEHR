import json
import os
from collections import Counter

disease_files = ["stroke", "multiple_sclerosis", "parkinson", "alzheimer", "huntington", "brain_tumor"]

fields_to_check = [
    "onset_pattern", "anatomical_location", "lesion_size", "lesion_characteristics",
    "imaging_modalities_used", "clinical_scales_used", "lab_tests", "genetic_testing",
    "differential_diagnoses_considered", "family_history", "medications_prescribed",
    "followup_duration_and_outcome", "multidisciplinary_team_involved"
]

NOT_MENTIONED_MARKERS = {"not mentioned", "none", "n/a", "not applicable", ""}

def is_real_value(v):
    """判断单个值是否算'真的有信息',排除各种形式的'未提及'标记"""
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip().lower() not in NOT_MENTIONED_MARKERS
    return True

def clean_values(val):
    """
    统一处理字段值,返回一个'干净的值列表'(可能为空列表)。
    - 如果是列表:过滤掉里面的'not mentioned'之类的假值
    - 如果是字符串:如果是'not mentioned'类,返回空列表;否则返回[值]
    """
    if val is None:
        return []
    if isinstance(val, list):
        return [v for v in val if is_real_value(v)]
    if isinstance(val, str):
        return [val] if is_real_value(val) else []
    return []

for disease in disease_files:
    filepath = f"data/by_disease/{disease}_canonical_facts.json"
    if not os.path.exists(filepath):
        continue
    with open(filepath, encoding="utf-8") as f:
        cases = json.load(f)

    total = len(cases)
    print(f"\n{'='*50}")
    print(f"{disease} (共{total}条)")
    print(f"{'='*50}")

    for field in fields_to_check:
        non_empty = 0
        all_values = []
        for c in cases:
            raw_val = c.get("canonical_facts", {}).get(field)
            cleaned = clean_values(raw_val)
            if cleaned:
                non_empty += 1
                all_values.extend(cleaned)

        rate = non_empty / total * 100 if total > 0 else 0
        print(f"\n  {field}: {non_empty}/{total} ({rate:.0f}%)")

        if all_values:
            top = Counter(all_values).most_common(5)
            for val, cnt in top:
                display_val = val if len(str(val)) < 100 else str(val)[:100] + "..."
                print(f"      - {display_val} ({cnt}次)")
