#!/usr/bin/env python3
"""
patient_session.py
Shared helpers: load a scenario's patient prompt and opening line, keep the conversation,
and save a transcript to runtime/transcripts/ (not committed to git).
"""
import datetime, pathlib, re, yaml
from gemma_client import ROOT, chat, model

SCEN = {"s1": "s1_pretest_counselling", "s2": "s2_disclosing_result", "s3": "s3_suicide_risk_assessment"}

class Session:
    def __init__(self, short):
        if short not in SCEN:
            raise SystemExit("Scenario must be one of: " + ", ".join(SCEN))
        self.short, self.sid = short, SCEN[short]
        prompt = (ROOT / "runtime" / "patient_prompts" / (self.sid + ".md")).read_text(encoding="utf-8")
        card = yaml.safe_load((ROOT / "scenarios" / self.sid / "role_card.yaml").read_text(encoding="utf-8"))
        self.opening = card["persona"]["opening_line"]
        self.name = card["persona"]["name"].split()[0]
        # The opening line is fixed, so every run starts the same way.
        self.msgs = [{"role": "system", "content": prompt}, {"role": "assistant", "content": self.opening}]
        self.log = [("Patient", self.opening)]

    def say(self, text, temperature=0.7):
        self.msgs.append({"role": "user", "content": text})
        reply = chat(self.msgs, temperature=temperature)
        self.msgs.append({"role": "assistant", "content": reply})
        self.log += [("Clinician", text), ("Patient", reply)]
        return reply

    def restart(self):
        self.msgs = self.msgs[:2]
        self.log.append(("Note", "--- new chat started ---"))
        self.log.append(("Patient", self.opening))

def save(sessions_or_logs, short, label):
    out_dir = ROOT / "runtime" / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    path = out_dir / f"{short}_{label}_{stamp}.md"
    lines = [f"# Transcript: {SCEN[short]}, {label}", f"Model: {model()}  ", f"Date: {stamp}", ""]
    for title, log in sessions_or_logs:
        if title:
            lines += [f"## {title}", ""]
        for who, text in log:
            if who == "Note":
                lines += [f"_{text}_", ""]
            else:
                lines += [f"**{who}:** {text}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
