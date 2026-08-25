"""loopstation.py 단위 테스트 — python3 -m unittest discover -s loop-station/tests"""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import loopstation  # noqa: E402


def make_criteria(scores):
    return [
        {"category": "정확성", "item": f"항목 {i + 1}", "score": s, "max": 5,
         "comment": "확인함"}
        for i, s in enumerate(scores)
    ]


def make_deduction(severity="minor", points=-1):
    return {"severity": severity, "points": points, "where": "2절",
            "reason": "오탈자", "fix_directive": "수정할 것"}


def make_record():
    """유효한 2회전 기록 (92점 → 98점 통과)."""
    r1_scores = [5] * 16 + [4, 4, 2, 2]  # 92
    r2_scores = [5] * 18 + [4, 4]        # 98
    return {
        "schema_version": 1,
        "run_id": "20260825-120000-sample-run",
        "created_at": "2026-08-25T12:00:00+09:00",
        "type": "education",
        "title": "샘플 수업 자료",
        "rubric": "loop-station/rubrics/education.md",
        "gate_threshold": 98,
        "requirements_summary": "샘플 요구사항",
        "deliverables": [
            {"path": "loop-station/deliverables/20260825-120000-sample-run/out.html",
             "format": "html", "description": "샘플 산출물"}
        ],
        "iterations": [
            {"round": 1, "total": 92, "criteria": make_criteria(r1_scores),
             "deductions": [make_deduction("major", -3),
                            make_deduction("major", -3),
                            make_deduction("minor", -1),
                            make_deduction("minor", -1)],
             "verdict": "revise"},
            {"round": 2, "total": 98, "criteria": make_criteria(r2_scores),
             "deductions": [make_deduction("minor", -1),
                            make_deduction("minor", -1)],
             "verdict": "pass"},
        ],
        "final_total": 98,
        "passed": True,
        "notes": "",
    }


class ValidateTests(unittest.TestCase):
    def test_valid_record_passes(self):
        self.assertEqual(loopstation.validate_record(make_record()), [])

    def assert_invalid(self, rec, fragment):
        errors = loopstation.validate_record(rec)
        self.assertTrue(errors, "오류가 검출되어야 합니다")
        self.assertTrue(any(fragment in e for e in errors),
                        f"'{fragment}' 포함 오류 기대, 실제: {errors}")

    def test_missing_title(self):
        rec = make_record()
        del rec["title"]
        self.assert_invalid(rec, "title")

    def test_bad_run_id(self):
        rec = make_record()
        rec["run_id"] = "Sample_Run!"
        self.assert_invalid(rec, "run_id")

    def test_bad_type(self):
        rec = make_record()
        rec["type"] = "unknown"
        self.assert_invalid(rec, "type")

    def test_score_out_of_range(self):
        rec = make_record()
        rec["iterations"][1]["criteria"][0]["score"] = 6
        self.assert_invalid(rec, "score")

    def test_total_mismatch(self):
        rec = make_record()
        rec["iterations"][1]["total"] = 99
        rec["final_total"] = 99
        self.assert_invalid(rec, "항목 점수 합")

    def test_passed_inconsistency(self):
        rec = make_record()
        rec["passed"] = False
        self.assert_invalid(rec, "모순")

    def test_final_total_mismatch(self):
        rec = make_record()
        rec["final_total"] = 100
        self.assert_invalid(rec, "final_total")

    def test_too_many_iterations(self):
        rec = make_record()
        extra = copy.deepcopy(rec["iterations"][0])
        rec["iterations"] = [copy.deepcopy(rec["iterations"][0]) for _ in range(6)]
        for i, it in enumerate(rec["iterations"]):
            it["round"] = i + 1
        rec["iterations"][-1] = extra
        rec["iterations"][-1]["round"] = 6
        rec["final_total"] = rec["iterations"][-1]["total"]
        rec["passed"] = False
        self.assert_invalid(rec, "최대 5회전")

    def test_round1_cap(self):
        rec = make_record()
        rec["iterations"][0]["criteria"] = make_criteria([5] * 19 + [3])  # 98
        rec["iterations"][0]["total"] = 98
        self.assert_invalid(rec, "95점 상한")

    def test_round1_min_deductions(self):
        rec = make_record()
        rec["iterations"][0]["deductions"] = [make_deduction()]
        self.assert_invalid(rec, "3건 이상")

    def test_anchor_rule_major_in_final(self):
        rec = make_record()
        rec["iterations"][1]["deductions"] = [make_deduction("major", -3)]
        self.assert_invalid(rec, "앵커 규칙")

    def test_anchor_rule_three_minors(self):
        rec = make_record()
        rec["iterations"][1]["deductions"] = [make_deduction() for _ in range(3)]
        self.assert_invalid(rec, "앵커 규칙")

    def test_last_verdict_must_match(self):
        rec = make_record()
        rec["iterations"][1]["verdict"] = "revise"
        self.assert_invalid(rec, "verdict")

    def test_comment_required(self):
        rec = make_record()
        rec["iterations"][1]["criteria"][0]["comment"] = ""
        self.assert_invalid(rec, "comment")


class FileValidationTests(unittest.TestCase):
    def test_filename_must_match_run_id(self):
        rec = make_record()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrong-name.json"
            path.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
            _, errors = loopstation.load_and_validate(path)
            self.assertTrue(any("파일명" in e for e in errors))

    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("{broken", encoding="utf-8")
            rec, errors = loopstation.load_and_validate(path)
            self.assertIsNone(rec)
            self.assertTrue(any("JSON" in e for e in errors))


class BuildTests(unittest.TestCase):
    def write_record(self, tmp, rec):
        records = Path(tmp) / "records"
        records.mkdir()
        (records / f"{rec['run_id']}.json").write_text(
            json.dumps(rec, ensure_ascii=False), encoding="utf-8")
        return records

    def test_build_renders_index_and_run_page(self):
        rec = make_record()
        with tempfile.TemporaryDirectory() as tmp:
            records = self.write_record(tmp, rec)
            site = Path(tmp) / "site"
            written = loopstation.build(records, site)
            names = {p.name for p in written}
            self.assertIn("index.html", names)
            self.assertIn(f"run-{rec['run_id']}.html", names)
            index_html = (site / "index.html").read_text(encoding="utf-8")
            self.assertIn(rec["run_id"], index_html)
            self.assertIn('lang="ko"', index_html)
            self.assertIn("prefers-color-scheme", index_html)
            run_html = (site / f"run-{rec['run_id']}.html").read_text(encoding="utf-8")
            self.assertIn("98/100", run_html)
            self.assertIn("회전별 점수 추이", run_html)

    def test_html_escaping(self):
        rec = make_record()
        rec["title"] = "<script>alert(1)</script>"
        with tempfile.TemporaryDirectory() as tmp:
            records = self.write_record(tmp, rec)
            site = Path(tmp) / "site"
            loopstation.build(records, site)
            run_html = (site / f"run-{rec['run_id']}.html").read_text(encoding="utf-8")
            self.assertNotIn("<script>alert", run_html)
            self.assertIn("&lt;script&gt;", run_html)

    def test_build_is_idempotent(self):
        rec = make_record()
        with tempfile.TemporaryDirectory() as tmp:
            records = self.write_record(tmp, rec)
            site = Path(tmp) / "site"
            loopstation.build(records, site)
            first = {p.name: p.read_bytes() for p in site.iterdir()}
            loopstation.build(records, site)
            second = {p.name: p.read_bytes() for p in site.iterdir()}
            self.assertEqual(first, second)

    def test_build_aborts_on_invalid_record(self):
        rec = make_record()
        rec["passed"] = False
        with tempfile.TemporaryDirectory() as tmp:
            records = self.write_record(tmp, rec)
            site = Path(tmp) / "site"
            with self.assertRaises(SystemExit):
                loopstation.build(records, site)


class SkeletonTests(unittest.TestCase):
    def test_skeleton_has_required_keys(self):
        sk = loopstation.skeleton("education", "제목")
        for key in ("schema_version", "run_id", "type", "iterations",
                    "final_total", "passed"):
            self.assertIn(key, sk)
        self.assertEqual(sk["gate_threshold"], 98)


if __name__ == "__main__":
    unittest.main()
