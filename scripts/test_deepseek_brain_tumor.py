import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

def read_file(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

layer1 = read_file("prompts/layer1_general_template.md")
layer2 = read_file("prompts/layer2_disease_modules/brain_tumor.md")
layer3_dx = read_file("prompts/layer3_guidelines/brain_tumor/diagnosis.yaml.md")
layer3_tx = read_file("prompts/layer3_guidelines/brain_tumor/treatment.yaml.md")
layer3_common = read_file("prompts/layer3_guidelines/common/medication_safety.yaml.md")

SYSTEM_PROMPT_BASE = """You are a senior neuro-oncologist designing a FICTIONAL patient for a
synthetic medical record dataset. No real person may be described. Produce a Canonical Facts
Sheet as YAML, following exactly the schema given to you.

Rules:
1. Every field in the provided disease module must be filled with a concrete, clinically coherent
   value, or explicitly "not applicable" / "not performed" if genuinely not relevant.
2. Values must be internally consistent.
3. Give exact dates for all timeline events; dates must be in chronological order.
4. differential[].status must be "not_supported" for every diagnosis considered and ruled out,
   with specific evidence. Never include the final diagnosis itself.
5. Every severity score and drug dose must be attached to a date.
6. key_consistency_facts must list the specific values a later document must not contradict.
7. Output YAML only.

--- LAYER 1: GENERAL TEMPLATE ---
{layer1}

--- LAYER 2: DISEASE MODULE (Brain Tumor) ---
{layer2}
"""

USER_PROMPT = """Generate a Canonical Facts Sheet for a fictional adult patient newly diagnosed
with a high-grade glioma who requires molecular workup and is about to start standard
chemoradiotherapy. Include the full treatment plan (both concurrent and adjuvant phases, with
specific doses and monitoring) in the treatment fields."""

def run(condition_name, system_prompt):
    print(f"\n{'='*60}\n{condition_name}\n{'='*60}")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": USER_PROMPT}
        ],
        temperature=0.3
    )
    output = response.choices[0].message.content
    print(output)
    filename = f"test_output_brain_tumor_{condition_name}.yaml"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\n已保存到 {filename}")
    return output

system_no_guidance = SYSTEM_PROMPT_BASE.format(layer1=layer1, layer2=layer2)
run("no_layer3", system_no_guidance)

system_with_guidance = SYSTEM_PROMPT_BASE.format(layer1=layer1, layer2=layer2) + f"""

--- LAYER 3: CLINICAL GUIDANCE (must be followed exactly for dosing, diagnostic criteria, and safety) ---
{layer3_common}

{layer3_dx}

{layer3_tx}
"""
run("with_layer3", system_with_guidance)

print("\n\n重点核对 with_layer3 版本:")
print("1. 同步期剂量是否为75mg/m²(不是150-200)")
print("2. 辅助期剂量是否为150-200mg/m²,第1-5天,28天一周期")
print("3. 是否提到PJP预防用药")
print("4. CBC监测频率是否为同步期每周一次")
print("5. 分子标记是否体现了TERT/EGFR/+7-10任一项即可诊断grade4(如果是IDH野生型病例)")
