import json
import os
import time
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

SYSTEM_PROMPT = """你是一名神经科临床数据提取专家。给你一段病例报告全文,请提取以下结构化信息,严格按JSON格式输出,不要输出任何多余文字。如果某项信息文中没有提及,填"not mentioned",不要编造。

{
  "chief_complaint": "string, 主诉,用简短英文概括",
  "onset_pattern": "acute/subacute/chronic/relapsing-remitting/progressive/not mentioned",
  "symptom_duration_before_presentation": "string, 症状持续多久才就诊,如'3 months', 'not mentioned'",
  "key_symptoms": ["array of strings, 核心症状/体征列表"],
  "anatomical_location": "string, 病灶解剖定位(如有), 否则'not mentioned'",
  "lesion_size": "string, 病灶大小(如有), 否则'not mentioned'",
  "lesion_characteristics": "string, 病灶影像学特征描述(强化方式/信号特点等), 否则'not mentioned'",
  "imaging_modalities_used": ["array, 用到的影像检查, 如MRI/CT/SPECT/PET"],
  "clinical_scales_used": ["array, 用到的临床量表及分数, 如'MMSE 20/30', 'EDSS 4.5'"],
  "lab_tests": ["array, 提到的实验室检查项目"],
  "genetic_testing": "string, 基因检测结果(如有), 否则'not mentioned'",
  "differential_diagnoses_considered": ["array, 明确提到考虑过、后排除的其他诊断"],
  "final_diagnosis": "string, 最终诊断",
  "family_history": "string, 简要总结家族史, 否则'not mentioned'",
  "medications_prescribed": ["array, 处方药物及剂量"],
  "treatment_response_or_side_effects": "string, 治疗反应或副作用, 否则'not mentioned'",
  "followup_duration_and_outcome": "string, 随访时长及结局, 否则'not mentioned'",
  "multidisciplinary_team_involved": ["array, 提到的参与科室/专家, 如'neurosurgery', 'radiology'"]
}"""

def extract_facts(case_text):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": case_text[:4000]}
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
    filepath = f"data/by_disease/{disease}_cases_valid_primary.json"
    if not os.path.exists(filepath):
        print(f"跳过 {disease}(文件不存在)")
        continue
    with open(filepath, encoding="utf-8") as f:
        cases = json.load(f)

    print(f"\n开始提取 {disease} 的canonical facts, 共 {len(cases)} 条...")
    extracted = []

    for i, case in enumerate(cases):
        facts = extract_facts(case["case_text"])
        if facts is None:
            continue
        case["canonical_facts"] = facts
        extracted.append(case)

        if (i + 1) % 10 == 0:
            print(f"  已处理 {i+1}/{len(cases)}")
        time.sleep(0.3)

    with open(f"data/by_disease/{disease}_canonical_facts.json", "w", encoding="utf-8") as f:
        json.dump(extracted, f, ensure_ascii=False, indent=2)

    print(f"{disease}: 完成 {len(extracted)} 条facts提取")

print("\n全部完成。")
