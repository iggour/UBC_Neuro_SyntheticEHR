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
facts_sheet = read_file("test_output_huntington_with_layer3.yaml")

# ---------- Stage 2: 用Facts Sheet生成正式英文病历正文 ----------

STAGE2_SYSTEM = f"""You are writing one clinical document for a FICTIONAL patient in a synthetic
dataset. You will receive a Canonical Facts Sheet. Write a full Neurology Consultation note.

DOCUMENT COMPLETENESS: follow exactly the 12-section skeleton below, including subsections
10.1-10.5 under Investigations. Never drop a section; write "Not applicable" if empty.

{layer1}

FACT DISCIPLINE
- The Canonical Facts Sheet is the single source of truth. Copy anchored values exactly.
- Do not use bracket placeholders for clinician names; invent specific fictitious full names.
- Reproduce the medication titration schedule from the Facts Sheet exactly, do not simplify it.
- Output the full clinical note as plain text (not YAML).
"""

STAGE2_USER = f"""Canonical Facts Sheet:
{facts_sheet}

Write the full Neurology Consultation document now, in English."""

print("="*60)
print("Stage 2: 生成英文病历正文")
print("="*60)
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": STAGE2_SYSTEM},
        {"role": "user", "content": STAGE2_USER}
    ],
    temperature=0.3
)
english_note = response.choices[0].message.content
print(english_note)
with open("test_output_huntington_note_en.md", "w", encoding="utf-8") as f:
    f.write(english_note)
print("\n已保存到 test_output_huntington_note_en.md")

# ---------- 单独一次调用:翻译成中文,不改内容 ----------

TRANSLATE_SYSTEM = """You are a professional medical translator. Translate the following English
clinical document into Chinese (Simplified). Rules:
1. Keep all numbers, dates, doses, lab values, and scale scores exactly as in the English version.
   Do not round, re-calculate, or alter any number.
2. Keep drug names in a form a Chinese-speaking clinician would recognize (add the Chinese generic
   name where a standard one exists; keep the English name in parentheses if uncertain).
3. Keep the same 12-section structure and section numbering.
4. Do not add, omit, or reinterpret any clinical content. This is a translation task, not a
   rewriting task.
5. Output the translated document only, no commentary."""

print("\n" + "="*60)
print("翻译成中文")
print("="*60)
response2 = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": TRANSLATE_SYSTEM},
        {"role": "user", "content": english_note}
    ],
    temperature=0.1
)
chinese_note = response2.choices[0].message.content
print(chinese_note)
with open("test_output_huntington_note_zh.md", "w", encoding="utf-8") as f:
    f.write(chinese_note)
print("\n已保存到 test_output_huntington_note_zh.md")
