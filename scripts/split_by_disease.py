import json
import os

with open("data/raw/neuro_cases_raw.json") as f:
    data = json.load(f)

disease_groups = {
    "stroke": ["stroke", "cerebral infarct", "cerebral ischemi", "brain infarct",
               "intracerebral hemorrhage", "cerebral hemorrhage", "subarachnoid hemorrhage"],
    "multiple_sclerosis": ["multiple sclerosis", "demyelinat"],
    "parkinson": ["parkinson's disease", "parkinsonism"],
    "alzheimer": ["alzheimer"],
    "huntington": ["huntington's disease", "huntington disease"],
    "brain_tumor": ["brain tumor", "brain tumour", "glioma", "glioblastoma", "meningioma", "astrocytoma"]
}

os.makedirs("data/by_disease", exist_ok=True)

for disease, kw_list in disease_groups.items():
    subset = [c for c in data if any(kw in c["matched_keywords"] for kw in kw_list)]
    outpath = f"data/by_disease/{disease}_cases.json"
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(subset, f, ensure_ascii=False, indent=2)
    print(f"{disease}: {len(subset)} 条 -> {outpath}")

print("\n全部拆分完成。")
