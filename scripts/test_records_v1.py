#!/usr/bin/env python3
"""
test_records_v1.py
Tests check 7 of check_publish_v1.py: injects one known error at a time into a temporary copy of the
synthetic reports and confirms that the checker reports a FAIL. The real files are not touched.

Usage:
    python3 scripts/test_records_v1.py
"""
import datetime, pathlib, shutil, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import check_publish_v1 as cp

ROOT = pathlib.Path(__file__).resolve().parent.parent
TODAY = datetime.date.today()
B1, B3, C42 = "B1_late_onset_diagnosis", "B3_late_stage_family_meeting", "C4-2_diagnosis_poor_insight"
R3, R4 = "records/case3_fraser.yaml", "records/case4_brennan.yaml"

# label, scenario row, file, old text, new text, text expected in the finding
INJECTED = [
    ("CAG wrong in the report text", B1, R3, "HTT CAG repeat sizes: 17 and 39", "HTT CAG repeat sizes: 17 and 41", "CAG 17/41"),
    ("Age wrong in the report text", C42, R4, "A 45-year-old man with about 18 months of irritability and problems at work, mild",
     "A 54-year-old man with about 18 months of irritability and problems at work, mild", "age 54"),
    ("Imaging too severe for the stage", B1, R3, "Mild volume loss in the caudate heads", "Marked volume loss in the caudate heads", "early-stage"),
    ("Date off the timeline", B3, R3, "month: 84", "month: 60", "timing says"),
    ("Medication not in the role card", B1, R3, "medications: [One blood pressure tablet a day]\n    label",
     "medications: [One blood pressure tablet a day, Tetrabenazine]\n    label", "tetrabenazine"),
]
OTHER_RULES = [
    ("Fictional label removed", B1, R3, 'label: "Synthetic – fictional patient"', 'label: "Report"', "label"),
    ("Abnormal result, role card says normal", C42, R4, '"1.9 mIU/L"', '"9.1 mIU/L"', "outside"),
    ("CAG quoted before it is known", C42, R4, "difficulty with a three-step command. Adopted, so family history is unknown. Looking",
     "difficulty with a three-step command. HTT CAG 17 / 42. Looking", "before it is known"),
    ("Hidden item copied into a report", C42, R4, "Cerebellum and\n          brainstem are normal.",
     "He drinks to switch off. Punched a hole in the kitchen door.", "hidden item"),
    ("Wrong stage field", B3, R3, "stage: late", "stage: early", "stage early"),
    ("Unknown knowledge card", B1, R3, "cards: [imaging-findings-in-hd,", "cards: [imaging-in-hd,", "unknown knowledge card"),
    ("Years since diagnosis wrong", B3, R3, "diagnosed seven years ago", "diagnosed four years ago", "diagnosed four"),
]


def fails(root):
    results, _, _ = cp.run(root, False, TODAY)
    return {n: [m for s, m in r[7] if s == cp.FAIL] for n, r in results.items()}


def run_set(title, cases, tmp):
    print(title)
    caught = 0
    for label, scenario, path, old, new, expect in cases:
        root = tmp / "repo"
        if root.exists():
            shutil.rmtree(root)
        root.mkdir()
        for name in ("scenarios", "records", "runtime/patient_prompts"):
            shutil.copytree(ROOT / name, root / name)
        (root / "web").mkdir()
        shutil.copy(ROOT / "web" / "hd_anchor_v2.html", root / "web")
        p = root / path
        text = p.read_text(encoding="utf-8")
        assert old in text, f"test setup: '{old}' not in {path}"
        p.write_text(text.replace(old, new), encoding="utf-8")
        hit = [m for m in fails(root)[scenario] if expect in m]
        caught += bool(hit)
        print(f"  {label:42}{'CAUGHT' if hit else 'MISSED':8}{hit[0][:80] if hit else ''}")
    print(f"  Detection rate: {caught}/{len(cases)}\n")
    return caught == len(cases)


def main():
    clean = sum(len(v) for v in fails(ROOT).values())
    print(f"Clean reports: {clean} FAIL(s) in check 7\n")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="records_test_"))
    try:
        ok = run_set("Five injected errors", INJECTED, tmp)
        ok = run_set("Other rules in check 7", OTHER_RULES, tmp) and ok
    finally:
        shutil.rmtree(tmp)
    sys.exit(0 if ok and clean == 0 else 1)


if __name__ == "__main__":
    main()
