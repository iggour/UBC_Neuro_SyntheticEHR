import json
import os
import time
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

SYSTEM_PROMPT = """你是一名神经科临床数据标注专家。给你一段病例报告全文,请判断以下内容,严格按JSON格式输出,不要输出任何多余文字:

{
  "is_valid_case": true/false,  // 是否是单一患者的病例叙事(不是综述/病例系列汇总/研究报告)
  "is_primary_complaint": true/false,  // 文中提到的神经系统疾病,是否是本次就诊/住院的主诉/核心诊断(而非既往史/排除诊断/顺带提及)
  "primary_diagnosis": "string",  // 本次病例的核心诊断(用简短英文术语,如果is_valid_case为false则填null)
  "has_clinical_scale": true/false,  // 是否提到疾病特异性评分量表(如EDSS, UPDRS, MMSE, MoCA, CDR, NIHSS等)
  "has_genetic_testing": true/false,  // 是否提到基因检测(如CAG重复数、APOE基因型等)
  "onset_pattern": "acute/subacute/chronic/relapsing-remitting/progressive/unknown",  // 起病模式
  "has_differential_diagnosis": true/false,  // 是否明确讨论了鉴别诊断/排除了其他可能诊断
  "has_family_history": true/false,  // 是否提到家族史
  "has_imaging": true/false,
  "has_labs": true/false,
  "has_medication": true/false,
  "has_followup": true/false
}"""

def annotate_case(case_text):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": case_text[:3000]}  # 截断过长文本,控制成本
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"  出错: {e}")
        return None

disease_files = ["stroke", "multiple_sclerosis", "parkinson", "alzheimer", "huntington", "brain_tumor"]

for disease in disease_files:
    filepath = f"data/by_disease/{disease}_cases.json"
    if not os.path.exists(filepath):
        continue
    with open(filepath, encoding="utf-8") as f:
        cases = json.load(f)

    print(f"\n开始处理 {disease}, 共 {len(cases)} 条...")
    annotated = []

    for i, case in enumerate(cases):
        result = annotate_case(case["case_text"])
        if result is None:
            continue
        case["llm_annotation"] = result
        annotated.append(case)

        if (i + 1) % 10 == 0:
            print(f"  已处理 {i+1}/{len(cases)}")
        time.sleep(0.3)  # 避免请求过快

    # 只保留真正有效、且主诉相关的病例
    valid_primary = [c for c in annotated if c["llm_annotation"]["is_valid_case"] and c["llm_annotation"]["is_primary_complaint"]]

    with open(f"data/by_disease/{disease}_cases_llm_annotated.json", "w", encoding="utf-8") as f:
        json.dump(annotated, f, ensure_ascii=False, indent=2)

    with open(f"data/by_disease/{disease}_cases_valid_primary.json", "w", encoding="utf-8") as f:
        json.dump(valid_primary, f, ensure_ascii=False, indent=2)

    print(f"{disease}: 全部标注{len(annotated)}条 -> 有效且主诉相关{len(valid_primary)}条")

print("\n全部完成。")
