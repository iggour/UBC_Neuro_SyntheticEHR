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
layer2 = read_file("prompts/layer2_disease_modules/huntington.md")
layer3_common = read_file("prompts/layer3_guidelines/common/medication_safety.yaml.md")
layer3_hd_dx = read_file("prompts/layer3_guidelines/huntington/diagnosis.yaml.md")
layer3_hd_tx = read_file("prompts/layer3_guidelines/huntington/treatment.yaml.md")

SYSTEM_PROMPT_BASE = """You are a senior neurologist designing a FICTIONAL patient for a synthetic
medical record dataset. No real person may be described. Produce a Canonical Facts Sheet as YAML,
following exactly the schema given to you. Do not add or rename top-level keys.

Rules:
1. Every field in the provided disease module must be filled with a concrete, clinically coherent
   value, or explicitly "not applicable" / "not performed" if genuinely not relevant.
2. Values must be internally consistent.
3. Give exact dates for all timeline events; dates must be in chronological order.
4. differential[].status must be "not_supported" for every diagnosis considered and ruled out,
   with specific evidence. Never include the final diagnosis itself.
5. Every severity score and drug dose must be attached to a date.
6. key_consistency_facts must list the specific values a later document must not contradict.
7. Output YAML only, no extra commentary.

--- LAYER 1: GENERAL TEMPLATE ---
{layer1}

--- LAYER 2: DISEASE MODULE (Huntington) ---
{layer2}
"""

USER_PROMPT = """Generate a Canonical Facts Sheet for a fictional adult patient newly diagnosed
with genetically confirmed Huntington disease who is about to start symptomatic treatment for
chorea. Include the full medication titration plan for the first several weeks in the
treatment.symptomatic field."""

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
    filename = f"test_output_huntington_{condition_name}.yaml"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\n已保存到 {filename}")
    return output

# 条件A: 不含layer3
system_no_guidance = SYSTEM_PROMPT_BASE.format(layer1=layer1, layer2=layer2)
run("no_layer3", system_no_guidance)

# 条件B: 含layer3
system_with_guidance = SYSTEM_PROMPT_BASE.format(layer1=layer1, layer2=layer2) + f"""

--- LAYER 3: CLINICAL GUIDANCE (must be followed exactly for dosing, safety, and interpretation) ---
{layer3_common}

{layer3_hd_dx}

{layer3_hd_tx}
"""
run("with_layer3", system_with_guidance)

print("\n\n两次生成完成。对比 test_output_huntington_no_layer3.yaml 与 test_output_huntington_with_layer3.yaml")
print("重点看 treatment.symptomatic 字段里的滴定方案是否符合: 第1周12.5mg qd, 第2周25mg分两次, 之后每周递增12.5mg。")
