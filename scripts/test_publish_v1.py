#!/usr/bin/env python3
"""
test_publish_v1.py
Tests check_publish_v1.py: injects one known error at a time into a temporary copy of the repo and
confirms that the check supposed to catch it reports the expected status. The real files are not touched.

Usage:
    python3 scripts/test_publish_v1.py
"""
import datetime, pathlib, re, shutil, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import check_publish_v1 as cp

ROOT = pathlib.Path(__file__).resolve().parent.parent
TODAY = datetime.date.today()


def sub(path, old, new, count=1):
    def apply(root):
        p = root / path
        t = p.read_text(encoding="utf-8")
        assert old in t, f"test setup: '{old}' not in {path}"
        p.write_text(t.replace(old, new, count), encoding="utf-8")
    return apply


def add_line(path, line):
    def apply(root):
        p = root / path
        p.write_text(p.read_text(encoding="utf-8") + "\n" + line + "\n", encoding="utf-8")
    return apply


def drop_source_field(path, pattern):
    def apply(root):
        p = root / path
        t = p.read_text(encoding="utf-8")
        new = re.sub(pattern, "", t)
        assert new != t, f"test setup: pattern not found in {path}"
        p.write_text(new, encoding="utf-8")
    return apply


S3, A1, A2, B1, C4 = ("scenarios/s3_suicide_risk_assessment", "scenarios/A1_disclosing_jhd_diagnosis",
                      "scenarios/A2_school_seizures_safety", "scenarios/B1_late_onset_diagnosis",
                      "scenarios/C4-1_recognising_possible_hd")
# label, scenario, check, expected status, mutation; `expect` text must appear in the finding
CASES = [
    ("CAG value impossible", "A1_disclosing_jhd_diagnosis", 1, "FAIL", sub(A1 + "/role_card.yaml", "HTT CAG repeats of 18 and 71", "HTT CAG repeats of 18 and 171")),
    ("CAG category wrong", "B1_late_onset_diagnosis", 1, "FAIL", sub(B1 + "/role_card.yaml", "39 repeats is in the reduced-penetrance range", "39 repeats is in the intermediate range")),
    ("Age impossible", "s3_suicide_risk_assessment", 1, "FAIL", sub(S3 + "/role_card.yaml", "age: 54", "age: 154")),
    ("Late onset at a young age", "B1_late_onset_diagnosis", 1, "FAIL", sub(B1 + "/role_card.yaml", "Ruth: 68", "Ruth: 48")),
    ("Family CAG differs", "A2_school_seizures_safety", 2, "FAIL", sub(A2 + "/role_card.yaml", '"18 / 71"', '"18 / 72"')),
    ("Family age goes down", "A2_school_seizures_safety", 2, "FAIL", sub(A2 + "/role_card.yaml", "Maya: 15", "Maya: 13")),
    ("Case 1 age jumps", "s3_suicide_risk_assessment", 2, "FAIL", sub(S3 + "/role_card.yaml", "age: 54", "age: 59")),
    ("Surname differs", "s3_suicide_risk_assessment", 2, "WARN", sub(S3 + "/role_card.yaml", "name: Teresa Moreno", "name: Teresa Morales")),
    ("Medication dropped in family", "A3_sibling_predictive_request", 2, "WARN", lambda r: None),
    ("Source URL missing", "s3_suicide_risk_assessment", 3, "FAIL", drop_source_field(S3 + "/checkpoints.yaml", r"https://www\.hikma\.com/\S+")),
    ("Check date missing", "s3_suicide_risk_assessment", 3, "FAIL", drop_source_field(S3 + "/checkpoints.yaml", r"verified by human reviewer 2026-10-26\.")),
    ("Disclaimer removed", "s1_pretest_counselling", 3, "FAIL", sub("scenarios/s1_pretest_counselling/family_prep_sheet.md", "Not medical advice.", "")),
    ("9-8-8 removed", "s3_suicide_risk_assessment", 3, "FAIL", lambda r: [(p.write_text(p.read_text(encoding="utf-8").replace("9-8-8", "crisis line"), encoding="utf-8")) for p in (r / S3).glob("*") if p.suffix in (".yaml", ".md")]),
    ("Content warning removed", "s3_suicide_risk_assessment", 3, "FAIL", drop_source_field(S3 + "/role_card.yaml", r"  content_warning:.*\n")),
    ("Method detail added", "s3_suicide_risk_assessment", 4, "FAIL", add_line(S3 + "/knowledge_cards.md", "- She thought about suicide by overdose.")),
    ("Dose linked to self-harm", "s3_suicide_risk_assessment", 4, "FAIL", add_line(S3 + "/knowledge_cards.md", "- She said she would take 40 tablets to end her life.")),
    ("Prep sheet too hard", "s1_pretest_counselling", 6, "FAIL", add_line("scenarios/s1_pretest_counselling/family_prep_sheet.md", " ".join(["Multidisciplinary neuropsychiatric rehabilitation considerations necessitate comprehensive interdisciplinary consultation regarding individualised anticipatory management."] * 25))),
]


EXPECT = {"Source URL missing": "no source URL", "Check date missing": "no check date", "9-8-8 removed": "9-8-8", "Content warning removed": "no content warning"}


def check_order(results, scenario, check, want):
    return [x for x in results[scenario][check] if x[0] == want]


def main():
    caught = 0
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="publish_test_"))
    try:
        for label, scenario, check, want, mutate in CASES:
            root = tmp / "repo"
            if root.exists():
                shutil.rmtree(root)
            root.mkdir()
            for name in ("scenarios", "runtime/patient_prompts"):
                shutil.copytree(ROOT / name, root / name)
            (root / "web").mkdir()
            shutil.copy(ROOT / "web" / "hd_anchor_v2.html", root / "web")
            mutate(root)
            results, meta, _ = cp.run(root, False, TODAY)
            hit = [x for x in check_order(results, scenario, check, want) if EXPECT.get(label, "") in x[1]]
            caught += bool(hit)
            print(f"{label:34}Check {check}  {'CAUGHT' if hit else 'MISSED':8}{hit[0][1][:70] if hit else ''}")
        # high-risk scenarios never auto-pass, even with no findings at all
        results, meta, _ = cp.run(ROOT, False, TODAY)
        high_ok = all(m["decision"] != "auto-pass" for m in meta.values() if m["tier"] == "high")
        print(f"{'High risk never auto-passes':34}         {'CAUGHT' if high_ok else 'MISSED'}")
    finally:
        shutil.rmtree(tmp)
    print("-" * 90)
    print(f"Detection rate: {caught}/{len(CASES)}")
    sys.exit(0 if caught == len(CASES) and high_ok else 1)


if __name__ == "__main__":
    main()
