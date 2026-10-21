#!/usr/bin/env python3
"""
test_checker_v0.py

Tests check_consistency_v0.py in two ways:
  1. Baseline: the unchanged demo should produce no FAIL (false-alarm test).
  2. Injection: put one known error into a copy of the demo and see whether the check
     that is supposed to catch it reports FAIL (detection-rate test).

Usage:
    python3 scripts/test_checker_v0.py demos/huntington_demo_v2.md
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_consistency_v0 import run_checks, FAIL  # noqa: E402

# (name, check that should catch it, old text, new text)
INJECTIONS = [
    ("Score changed in one place (TMS 28 to 32)", "3",
     "- Total Motor Score (TMS): 28/124", "- Total Motor Score (TMS): 32/124"),
    ("CAG repeat number changed (42 to 38)", "3",
     "Genetically confirmed Huntington disease (42 CAG repeats)",
     "Genetically confirmed Huntington disease (38 CAG repeats)"),
    ("Addendum dated before the consultation", "2",
     "# Addendum: Genetic Result and Treatment Decision (2026-09-09)",
     "# Addendum: Genetic Result and Treatment Decision (2026-08-01)"),
    ("Later date written into the main note", "2",
     "HTT CAG repeat analysis sent 2026-08-19.", "HTT CAG repeat analysis sent 2026-09-20."),
    ("Wrong week-1 dose (12.5 mg changed to 25 mg)", "6",
     "12.5 mg once daily in the morning for the first week",
     "25 mg once daily in the morning for the first week"),
    ("Daily dose above 50 mg without CYP2D6", "6",
     "Doses of 37.5-50 mg/day will be given", "Doses of 37.5-75 mg/day will be given"),
    ("Final diagnosis listed as excluded", "5",
     "- Wilson disease: ceruloplasmin",
     "- Huntington disease: excluded on clinical grounds.\n- Wilson disease: ceruloplasmin"),
    ("Section removed (Social history heading)", "1",
     "## 7. Social history\n", ""),
]


def failed_checks(text):
    return {num for num, _, status, _ in run_checks(text) if status == FAIL}


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    text = open(sys.argv[1], encoding="utf-8").read()

    base = failed_checks(text)
    print(f"Baseline (unchanged demo): {len(base)} false alarm(s) {sorted(base) if base else ''}\n")

    caught = 0
    print(f"{'Injected error':48} {'Should be caught by':20} {'Result':10} Other checks that fired")
    print("-" * 110)
    for name, expected, old, new in INJECTIONS:
        if old not in text:
            print(f"{name:48} SKIPPED: target text not found in the demo")
            continue
        fired = failed_checks(text.replace(old, new, 1))
        ok = expected in fired
        caught += ok
        others = ", ".join(sorted(fired - {expected})) or "-"
        print(f"{name:48} Check {expected:14} {'CAUGHT' if ok else 'MISSED':10} {others}")
    n = len(INJECTIONS)
    print("-" * 110)
    print(f"Detection rate: {caught}/{n} = {caught / n:.0%}")
    sys.exit(0 if (caught == n and not base) else 1)


if __name__ == "__main__":
    main()
