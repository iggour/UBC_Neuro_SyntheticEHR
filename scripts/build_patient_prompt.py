#!/usr/bin/env python3
"""
build_patient_prompt.py
Turn a scenario role card into a system prompt for the AI-simulated patient.
The patient model sees persona, companion, facts, hidden items and behaviour rules.
It does NOT see the scenario brief for the trainee, learning goals, mentor_only, or checkpoints.

Usage:
    python3 scripts/build_patient_prompt.py scenarios/s3_suicide_risk_assessment/role_card.yaml
Output: runtime/patient_prompts/<scenario_id>.md
"""
import sys, pathlib, yaml

GENERAL_RULES = """You are role-playing a patient (and, if listed, the person with them) in a
training simulation for clinicians. The user is the clinician. Everything below is fictional.
- Speak only as the character(s). If a companion speaks, start the line with their name, e.g. "Luis: ...".
- Never give medical facts, numbers, guideline rules or advice that the character would not know.
- Never invent new medical facts about the character. If asked about something not listed, answer vaguely.
- Keep hidden items secret until the condition for revealing them is met.
- Never describe methods, amounts or details of self-harm."""

def dump(obj):
    return yaml.safe_dump(obj, allow_unicode=True, sort_keys=False, width=100).strip()

def main(path):
    card = yaml.safe_load(open(path, encoding="utf-8"))
    sid = card["scenario"]["id"]
    parts = ["# System prompt: simulated patient (" + sid + ")", "", "## General rules", GENERAL_RULES,
             "", "## Setting", card["scenario"]["setting"],
             "", "## Who you are", dump(card["persona"])]
    if "companion" in card:
        parts += ["", "## Person with you", dump(card["companion"])]
    parts += ["", "## Facts (never change these)", dump(card["facts"]),
              "", "## Hidden items (reveal only when the condition is met)", dump(card["hidden"])]
    if "expected_questions" in card:
        parts += ["", "## Questions to ask if the clinician has not covered them by about that turn",
                  dump(card["expected_questions"])]
    parts += ["", "## How to behave", "\n".join("- " + r for r in card["behaviour_rules"]),
              "", "Start the conversation with your opening line: " + card["persona"]["opening_line"]]
    out = pathlib.Path("runtime/patient_prompts") / (sid + ".md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(out, len(out.read_text()), "chars")

if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
