#!/usr/bin/env python3
"""
chat_patient.py
Talk to the AI-simulated patient in the terminal. You type as the clinician.
Usage:  python3 scripts/chat_patient.py s3
Commands:  /new = start again   /quit = save and exit
The transcript is saved to runtime/transcripts/ when you quit.
"""
import sys
from patient_session import Session, save

def main():
    short = sys.argv[1] if len(sys.argv) > 1 else "s3"
    s = Session(short)
    print(f"Scenario {short}. Type as the clinician. /new to restart, /quit to save and exit.\n")
    print(f"{s.name}: {s.opening}\n")
    try:
        while True:
            text = input("You: ").strip()
            if not text:
                continue
            if text == "/quit":
                break
            if text == "/new":
                s.restart(); print(f"\n--- new chat ---\n{s.name}: {s.opening}\n"); continue
            print(f"\n{s.name}: {s.say(text)}\n")
    except (KeyboardInterrupt, EOFError):
        print()
    print("Saved:", save([("", s.log)], short, "manual"))

if __name__ == "__main__":
    main()
