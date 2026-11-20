"""loopcanon.py 단위 테스트 — python3 -m unittest discover -s loop-station/tests"""

import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path

try:
    import loopcanon
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    import loopcanon

LS_DIR = Path(__file__).resolve().parent.parent  # loop-station/
REPO_ROOT = LS_DIR.parent
DIGEST = "weekly-special-pe-digest"
INQUIRY = "practicum-inquiry-triage"

FRI_0915 = datetime.fromisoformat("2026-11-20T09:15:00+09:00")  # 금요일
FRI_0920 = datetime.fromisoformat("2026-11-20T09:20:00+09:00")


def real_spec(loop_id):
    return json.loads(
        (LS_DIR / "loops" / f"{loop_id}.json").read_text(encoding="utf-8")
    )


def make_event(
    event_id="evt-1",
    subject="교생 실습 문의",
    body="특수체육 수업 관련 질문입니다",
    **kw,
):
    ev = {
        "id": event_id,
        "source": "email",
        "received_at": "2026-11-20T09:00:00+09:00",
        "subject": subject,
        "body": body,
    }
    ev.update(kw)
    return ev


def make_passing_record(run_id):
    """loopstation 98점 게이트를 통과하는 2회전 기록."""

    def crit(scores):
        return [
            {
                "category": "정확성",
                "item": f"항목 {i + 1}",
                "score": s,
                "max": 5,
                "comment": "확인함",
            }
            for i, s in enumerate(scores)
        ]

    ded = {
        "severity": "minor",
        "points": -1,
        "where": "본문",
        "reason": "어색한 문장",
        "fix_directive": "다듬기",
    }
    return {
        "schema_version": 1,
        "run_id": run_id,
        "created_at": "2026-11-20T10:00:00+09:00",
        "type": "document",
        "title": "다이제스트",
        "rubric": "loop-station/rubrics/document.md",
        "gate_threshold": 98,
        "requirements_summary": "주간 다이제스트",
        "deliverables": [{"path": "x", "format": "md", "description": "초안"}],
        "iterations": [
            {
                "round": 1,
                "total": 92,
                "criteria": crit([5] * 16 + [4, 4, 2, 2]),
                "deductions": [ded, ded, ded],
                "verdict": "revise",
            },
            {
                "round": 2,
                "total": 98,
                "criteria": crit([5] * 18 + [4, 4]),
                "deductions": [ded, ded],
                "verdict": "pass",
            },
        ],
        "final_total": 98,
        "passed": True,
        "notes": "",
    }


class SandboxTestCase(unittest.TestCase):
    """임시 저장소: <tmp>/loop-station/{loops,rubrics,...}. 실제 예시 명세를 복사해 쓴다."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        repo = Path(self._tmp.name)
        root = repo / "loop-station"
        (root / "loops").mkdir(parents=True)
        (root / "rubrics").mkdir()
        (root / "records").mkdir()
        shutil.copy(
            LS_DIR / "rubrics" / "document.md", root / "rubrics" / "document.md"
        )
        self.paths = loopcanon.Paths(root)
        for loop_id in (DIGEST, INQUIRY):
            self.write_spec(real_spec(loop_id))

    def tearDown(self):
        self._tmp.cleanup()

    def write_spec(self, spec):
        path = self.paths.loops / f"{spec['loop_id']}.json"
        path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        return spec

    def spec(self, loop_id):
        return loopcanon.load_spec(self.paths, loop_id)

    def write_workers(self, run_dir, outputs):
        for role, data in outputs.items():
            out = run_dir / "workers" / role / "output.json"
            out.write_text(
                data if isinstance(data, str) else json.dumps(data, ensure_ascii=False),
                encoding="utf-8",
            )

    def write_report(
        self,
        run_dir,
        summary="요약입니다",
        improvements=3,
        attach=True,
        resolutions=None,
    ):
        attachments = []
        if attach:
            (run_dir / "attachments" / "list.csv").write_text("doi\n", encoding="utf-8")
            attachments = ["attachments/list.csv"]
        report = {
            "summary": summary,
            "improvements": [f"제안 {i + 1}" for i in range(improvements)],
            "attachments": attachments,
            "resolutions": resolutions or {},
        }
        (run_dir / "report.json").write_text(
            json.dumps(report, ensure_ascii=False), encoding="utf-8"
        )

    def write_record(self, run_id):
        path = self.paths.records / f"{run_id}.json"
        path.write_text(
            json.dumps(make_passing_record(run_id), ensure_ascii=False),
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# 명세 검증
# ---------------------------------------------------------------------------


class TestSpecValidation(unittest.TestCase):
    def test_shipped_specs_are_valid(self):
        for path in sorted((LS_DIR / "loops").glob("*.json")):
            with self.subTest(path=path.name):
                _, errors = loopcanon.load_spec_file(path, REPO_ROOT)
                self.assertEqual(errors, [])

    def assert_error(self, mutate, fragment, loop_id=DIGEST):
        spec = copy.deepcopy(real_spec(loop_id))
        mutate(spec)
        errors = loopcanon.validate_spec(spec, REPO_ROOT)
        self.assertTrue(
            any(fragment in e for e in errors), f"{fragment!r} 없음: {errors}"
        )

    def test_bad_weekday(self):
        self.assert_error(
            lambda s: s["trigger"].update(weekdays=["friday"]), "trigger.weekdays"
        )

    def test_bad_time(self):
        self.assert_error(lambda s: s["trigger"].update(time="9:00"), "trigger.time")

    def test_window_crossing_midnight(self):
        self.assert_error(
            lambda s: s["trigger"].update(time="23:30", window_minutes=60), "자정"
        )

    def test_bad_offset(self):
        self.assert_error(lambda s: s["trigger"].update(utc_offset="KST"), "utc_offset")

    def test_event_requires_keywords(self):
        self.assert_error(
            lambda s: s["trigger"].update(any_keywords=[]), "any_keywords", INQUIRY
        )

    def test_connector_category(self):
        self.assert_error(
            lambda s: s["connectors"][0].update(category="chat"), "category"
        )

    def test_write_connector_requires_human_review(self):
        self.assert_error(
            lambda s: s["human_review"].update(required=False), "쓰기 커넥터"
        )

    def test_duplicate_subagent_role(self):
        def mutate(s):
            s["subagents"][1]["role"] = s["subagents"][0]["role"]

        self.assert_error(mutate, "role 중복")

    def test_path_mode_requires_steps(self):
        self.assert_error(
            lambda s: s["skill"].update(instruction_mode="path", steps=[]), "경로 지시"
        )

    def test_success_criteria_need_numbers(self):
        self.assert_error(
            lambda s: s["skill"].update(success_criteria=["요약을 짧게"]), "구체적 수치"
        )

    def test_prohibition_needs_reason(self):
        self.assert_error(
            lambda s: s["skill"]["prohibitions"][0].pop("reason"), "reason"
        )

    def test_rubric_must_exist(self):
        self.assert_error(
            lambda s: s["skill"]["self_check"].update(
                rubric="loop-station/rubrics/none.md"
            ),
            "파일이 없습니다",
        )

    def test_max_rounds_cap(self):
        self.assert_error(
            lambda s: s["stop_conditions"].update(max_rounds=6), "max_rounds"
        )

    def test_file_name_must_match_loop_id(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "wrong.json"
            path.write_text(json.dumps(real_spec(DIGEST)), encoding="utf-8")
            _, errors = loopcanon.load_spec_file(path, REPO_ROOT)
            self.assertTrue(any("파일명" in e for e in errors))


# ---------------------------------------------------------------------------
# 트리거
# ---------------------------------------------------------------------------


class TestTriggers(unittest.TestCase):
    def setUp(self):
        self.digest = real_spec(DIGEST)
        self.inquiry = real_spec(INQUIRY)

    def at(self, text):
        return datetime.fromisoformat(text)

    def test_schedule_inside_window(self):
        self.assertEqual(
            loopcanon.schedule_slot(self.digest, self.at("2026-11-20T09:59:59+09:00")),
            "2026-11-20T09:00:00+09:00",
        )

    def test_schedule_window_end_is_exclusive(self):
        self.assertIsNone(
            loopcanon.schedule_slot(self.digest, self.at("2026-11-20T10:00:00+09:00"))
        )

    def test_schedule_before_time_and_other_day(self):
        self.assertIsNone(
            loopcanon.schedule_slot(self.digest, self.at("2026-11-20T08:59:00+09:00"))
        )
        self.assertIsNone(
            loopcanon.schedule_slot(self.digest, self.at("2026-11-19T09:15:00+09:00"))
        )

    def test_schedule_converts_timezone(self):
        # 금요일 00:15 UTC = 금요일 09:15 KST
        self.assertIsNotNone(
            loopcanon.schedule_slot(self.digest, self.at("2026-11-20T00:15:00Z"))
        )
        # 목요일 23:00 UTC = 금요일 08:00 KST → 아직 아님
        self.assertIsNone(
            loopcanon.schedule_slot(self.digest, self.at("2026-11-19T23:00:00Z"))
        )

    def test_event_match_and_priority(self):
        self.assertEqual(loopcanon.match_event(self.inquiry, make_event()), "normal")
        self.assertEqual(
            loopcanon.match_event(
                self.inquiry, make_event(subject="실습 중 부상 긴급")
            ),
            "high",
        )
        self.assertEqual(
            loopcanon.match_event(self.inquiry, make_event(subject="[참고] 실습 일정")),
            "low",
        )

    def test_most_urgent_rule_wins(self):
        ev = make_event(subject="[참고] 오늘 실습 안전 공지")  # low + high 동시
        self.assertEqual(loopcanon.match_event(self.inquiry, ev), "high")

    def test_event_excluded_or_unrelated(self):
        self.assertIsNone(
            loopcanon.match_event(self.inquiry, make_event(body="실습 매트 광고"))
        )
        self.assertIsNone(
            loopcanon.match_event(
                self.inquiry, make_event(subject="회식", body="장소 안내")
            )
        )
        self.assertIsNone(
            loopcanon.match_event(self.inquiry, make_event(source="slack"))
        )

    def test_triage_orders_by_priority_then_arrival(self):
        events = [
            make_event("a", received_at="2026-11-20T08:00:00+09:00"),
            make_event(
                "b", subject="실습 사고 긴급", received_at="2026-11-20T09:30:00+09:00"
            ),
            make_event("c", received_at="2026-11-20T07:00:00+09:00"),
            make_event("d", subject="점심", body="메뉴"),
        ]
        queue, unmatched = loopcanon.triage([self.digest, self.inquiry], events)
        self.assertEqual([q["event_id"] for q in queue], ["b", "c", "a"])
        self.assertEqual(unmatched, ["d"])

    def test_naive_time_rejected(self):
        with self.assertRaises(loopcanon.LoopError):
            loopcanon.parse_time("2026-11-20T09:00:00")

    def test_validate_event(self):
        self.assertEqual(loopcanon.validate_event(make_event()), [])
        self.assertTrue(loopcanon.validate_event({"id": "x"}))


# ---------------------------------------------------------------------------
# 실행 생명주기: start → merge → check → review
# ---------------------------------------------------------------------------


class TestStart(SandboxTestCase):
    def test_start_creates_isolated_workspace_and_memory(self):
        run_dir = loopcanon.start_run(self.paths, self.spec(DIGEST), FRI_0915)
        self.assertEqual(run_dir.name, f"20261120-091500-{DIGEST}")
        for role in ("pubmed-collector", "scholar-collector", "library-auditor"):
            self.assertTrue((run_dir / "workers" / role).is_dir())
        self.assertTrue((run_dir / "attachments").is_dir())
        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        self.assertEqual((meta["status"], meta["round"]), ("running", 1))

        mem = loopcanon.Memory(self.paths, DIGEST)
        self.assertEqual(mem.state()["status"], "running")
        self.assertIn("특수체육", mem.context_path.read_text(encoding="utf-8"))
        self.assertTrue(mem.skill_path.is_file())
        self.assertEqual([h["event"] for h in mem.read("history")], ["started"])

    def test_not_due_is_refused(self):
        with self.assertRaisesRegex(loopcanon.LoopError, "예약 시각"):
            loopcanon.start_run(
                self.paths,
                self.spec(DIGEST),
                datetime.fromisoformat("2026-11-19T09:15:00+09:00"),
            )

    def test_concurrent_run_is_refused(self):
        loopcanon.start_run(self.paths, self.spec(DIGEST), FRI_0915)
        with self.assertRaisesRegex(loopcanon.LoopError, "진행 중인 실행"):
            loopcanon.start_run(self.paths, self.spec(DIGEST), FRI_0920)

    def test_same_slot_is_not_run_twice(self):
        loopcanon.start_run(self.paths, self.spec(DIGEST), FRI_0915)
        loopcanon.Memory(self.paths, DIGEST).save_state(
            status="done"
        )  # 끝난 것으로 간주
        with self.assertRaisesRegex(loopcanon.LoopError, "이미 처리한 트리거"):
            loopcanon.start_run(self.paths, self.spec(DIGEST), FRI_0920)

    def test_event_loop_requires_matching_event(self):
        spec = self.spec(INQUIRY)
        with self.assertRaisesRegex(loopcanon.LoopError, "--event"):
            loopcanon.start_run(self.paths, spec, FRI_0915)
        with self.assertRaisesRegex(loopcanon.LoopError, "맞지 않습니다"):
            loopcanon.start_run(
                self.paths, spec, FRI_0915, make_event(subject="점심", body="메뉴")
            )
        run_dir = loopcanon.start_run(
            self.paths, spec, FRI_0915, make_event(subject="실습 부상 긴급")
        )
        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["priority"], "high")

    def test_daily_cap_and_duplicate_event(self):
        spec = self.write_spec(
            dict(
                real_spec(INQUIRY),
                stop_conditions=dict(
                    real_spec(INQUIRY)["stop_conditions"], daily_run_cap=1
                ),
            )
        )
        mem = loopcanon.Memory(self.paths, INQUIRY)
        loopcanon.start_run(self.paths, spec, FRI_0915, make_event("e1"))
        mem.save_state(status="done")
        with self.assertRaisesRegex(loopcanon.LoopError, "이미 처리한 트리거"):
            loopcanon.start_run(self.paths, spec, FRI_0920, make_event("e1"))
        with self.assertRaisesRegex(loopcanon.LoopError, "일일 실행 상한"):
            loopcanon.start_run(self.paths, spec, FRI_0920, make_event("e2"))
        self.assertEqual(mem.read("history")[-1]["event"], "blocked")
        # 다음 날은 다시 가능
        loopcanon.start_run(
            self.paths,
            spec,
            datetime.fromisoformat("2026-11-21T09:00:00+09:00"),
            make_event("e2"),
        )

    def test_corrupt_memory_fails_closed(self):
        mem = loopcanon.Memory(self.paths, DIGEST)
        mem.ensure(self.spec(DIGEST))
        mem.history_path.write_text(
            '{"event": "started"}\n{깨진 줄\n', encoding="utf-8"
        )
        with self.assertRaisesRegex(loopcanon.LoopError, "메모리 손상"):
            loopcanon.start_run(self.paths, self.spec(DIGEST), FRI_0915)


class TestMerge(SandboxTestCase):
    def setUp(self):
        super().setUp()
        self.run_dir = loopcanon.start_run(self.paths, self.spec(DIGEST), FRI_0915)

    def test_merge_marks_conflicts_and_isolates_failures(self):
        a = {"findings": {"doi:1": "요지 A", "doi:2": "같음"}}
        b = {"findings": {"doi:1": "요지 B", "doi:2": "같음", "doi:3": "B만"}}
        self.write_workers(
            self.run_dir, {"pubmed-collector": a, "scholar-collector": b}
        )
        # library-auditor는 산출물 없음 → 실패로 격리
        before = (self.run_dir / "workers/pubmed-collector/output.json").read_text(
            encoding="utf-8"
        )

        result = loopcanon.merge_run(self.paths, self.run_dir)

        self.assertEqual(result["merged"], {"doi:2": "같음", "doi:3": "B만"})
        self.assertEqual(
            result["agreed_by"]["doi:2"], ["pubmed-collector", "scholar-collector"]
        )
        self.assertEqual(
            result["conflicts"],
            [
                {
                    "key": "doi:1",
                    "values": {
                        "pubmed-collector": "요지 A",
                        "scholar-collector": "요지 B",
                    },
                }
            ],
        )
        self.assertEqual(
            [f["role"] for f in result["failed_workers"]], ["library-auditor"]
        )
        # 각자의 결과는 그대로 남는다
        self.assertEqual(
            (self.run_dir / "workers/pubmed-collector/output.json").read_text(
                encoding="utf-8"
            ),
            before,
        )
        self.assertTrue((self.run_dir / "merged.json").is_file())

    def test_conflict_keeps_every_agreeing_side(self):
        self.write_workers(
            self.run_dir,
            {
                "pubmed-collector": {"findings": {"k": 1}},
                "scholar-collector": {"findings": {"k": 1}},
                "library-auditor": {"findings": {"k": 2}},
            },
        )
        result = loopcanon.merge_run(self.paths, self.run_dir)
        self.assertEqual(
            result["conflicts"][0]["values"],
            {"pubmed-collector": 1, "scholar-collector": 1, "library-auditor": 2},
        )

    def test_corrupt_output_is_failure_not_crash(self):
        self.write_workers(
            self.run_dir,
            {"pubmed-collector": "{깨짐", "scholar-collector": {"findings": {"k": 1}}},
        )
        result = loopcanon.merge_run(self.paths, self.run_dir)
        self.assertEqual(result["ok_workers"], ["scholar-collector"])
        self.assertEqual(len(result["failed_workers"]), 2)

    def test_all_failed_is_refused(self):
        with self.assertRaisesRegex(loopcanon.LoopError, "모든 서브에이전트"):
            loopcanon.merge_run(self.paths, self.run_dir)


class TestCheckAndReview(SandboxTestCase):
    def start_merged(self, loop_id=DIGEST, conflict=False):
        spec = self.spec(loop_id)
        event = make_event() if spec["trigger"]["type"] == "event" else None
        run_dir = loopcanon.start_run(self.paths, spec, FRI_0915, event)
        roles = [w["role"] for w in spec["subagents"]]
        outputs = {r: {"findings": {f"{r}:item": "ok"}} for r in roles}
        if conflict:
            outputs[roles[0]]["findings"]["shared"] = "A"
            outputs[roles[1]]["findings"]["shared"] = "B"
        self.write_workers(run_dir, outputs)
        loopcanon.merge_run(self.paths, run_dir)
        return run_dir

    def meta(self, run_dir):
        return json.loads((run_dir / "run.json").read_text(encoding="utf-8"))

    def test_failing_check_lists_problems_and_advances_round(self):
        run_dir = self.start_merged(conflict=True)
        self.write_report(run_dir, summary="가" * 201, improvements=2, attach=False)
        ev = loopcanon.check_run(self.paths, run_dir)
        self.assertFalse(ev["passed"])
        text = "\n".join(ev["problems"])
        for fragment in (
            "201자",
            "개선 제안 2건",
            "첨부 파일 0개",
            "충돌 미해결",
            "자가진단 기록이 없습니다",
        ):
            self.assertIn(fragment, text)
        self.assertEqual(
            (self.meta(run_dir)["status"], self.meta(run_dir)["round"]), ("running", 2)
        )
        self.assertEqual(
            loopcanon.Memory(self.paths, DIGEST).read("evaluations")[-1]["round"], 1
        )

    def test_summary_exactly_at_limit_passes(self):
        run_dir = self.start_merged()
        self.write_report(run_dir, summary="가" * 200)
        self.write_record(run_dir.name)
        ev = loopcanon.check_run(self.paths, run_dir)
        self.assertEqual(ev["problems"], [])
        self.assertEqual(ev["metrics"]["gate_score"], 98)
        self.assertEqual(self.meta(run_dir)["status"], "awaiting_review")

    def test_resolved_conflict_passes(self):
        run_dir = self.start_merged(conflict=True)
        self.write_report(run_dir, resolutions={"shared": "A 채택 — 원문 DOI 확인"})
        self.write_record(run_dir.name)
        self.assertTrue(loopcanon.check_run(self.paths, run_dir)["passed"])

    def test_attachment_outside_run_dir_rejected(self):
        run_dir = self.start_merged()
        self.write_report(run_dir)
        report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
        report["attachments"] = ["../../../loops/weekly-special-pe-digest.json"]
        (run_dir / "report.json").write_text(json.dumps(report), encoding="utf-8")
        self.write_record(run_dir.name)
        ev = loopcanon.check_run(self.paths, run_dir)
        self.assertTrue(any("실행 폴더 밖" in p for p in ev["problems"]))

    def test_halts_at_max_rounds(self):
        run_dir = self.start_merged(INQUIRY)  # max_rounds 3, gate_record false
        self.write_report(run_dir, improvements=0)
        for expected_round in (1, 2, 3):
            ev = loopcanon.check_run(self.paths, run_dir)
            self.assertEqual(ev["round"], expected_round)
        self.assertEqual(ev["next_status"], "halted")
        self.assertEqual(
            loopcanon.Memory(self.paths, INQUIRY).state()["status"], "halted"
        )
        with self.assertRaisesRegex(loopcanon.LoopError, "진행 중인 실행만"):
            loopcanon.check_run(self.paths, run_dir)

    def test_review_approve_finishes_and_grows_skill_memory(self):
        run_dir = self.start_merged(INQUIRY)
        self.write_report(run_dir)
        with self.assertRaisesRegex(loopcanon.LoopError, "사람 검토 대기"):
            loopcanon.review_run(
                self.paths, run_dir, decision="approve", reviewer="교수", note="확인"
            )
        self.assertTrue(loopcanon.check_run(self.paths, run_dir)["passed"])
        loopcanon.review_run(
            self.paths,
            run_dir,
            decision="approve",
            reviewer="교수",
            note="발송 승인",
            lesson="부상 문의는 보호자 연락 절차를 첫 줄에",
            at=FRI_0920,
        )
        mem = loopcanon.Memory(self.paths, INQUIRY)
        self.assertEqual(mem.state()["status"], "done")
        self.assertIn("보호자 연락 절차", mem.skill_path.read_text(encoding="utf-8"))
        kinds = [e["kind"] for e in mem.read("evaluations")]
        self.assertEqual(kinds, ["self_check", "human_review"])

    def test_review_revise_reopens_next_round(self):
        run_dir = self.start_merged(INQUIRY)
        self.write_report(run_dir)
        loopcanon.check_run(self.paths, run_dir)
        loopcanon.review_run(
            self.paths, run_dir, decision="revise", reviewer="교수", note="근거 보강"
        )
        self.assertEqual(
            (self.meta(run_dir)["status"], self.meta(run_dir)["round"]), ("running", 2)
        )

    def test_review_requires_note(self):
        run_dir = self.start_merged(INQUIRY)
        self.write_report(run_dir)
        loopcanon.check_run(self.paths, run_dir)
        with self.assertRaisesRegex(loopcanon.LoopError, "비워 둘 수 없습니다"):
            loopcanon.review_run(
                self.paths, run_dir, decision="approve", reviewer="교수", note=" "
            )


class TestCli(SandboxTestCase):
    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = loopcanon.main(["--root", str(self.paths.root), *args])
        return code, out.getvalue() + err.getvalue()

    def test_full_cycle_via_cli(self):
        code, out = self.run_cli("validate")
        self.assertEqual(code, 0, out)
        code, out = self.run_cli("due", "--at", "2026-11-20T09:15:00+09:00")
        self.assertIn(DIGEST, out)

        events = self.paths.root / "events.json"
        events.write_text(
            json.dumps([make_event("x", subject="실습 사고 긴급")]), encoding="utf-8"
        )
        code, out = self.run_cli("match", "--event", str(events))
        self.assertIn("[긴급] x", out)

        code, out = self.run_cli(
            "start",
            INQUIRY,
            "--at",
            "2026-11-20T09:15:00+09:00",
            "--event",
            str(events),
        )
        self.assertEqual(code, 0, out)
        run_id = f"20261120-091500-{INQUIRY}"
        run_dir = self.paths.runs / INQUIRY / run_id
        self.write_workers(
            run_dir, {"manual-searcher": {"findings": {"절차": "영역③"}}}
        )

        self.assertEqual(self.run_cli("merge", run_id)[0], 0)
        code, out = self.run_cli("check", run_id)
        self.assertEqual(code, 1)  # 보고서가 빈 스켈레톤
        self.write_report(run_dir)
        code, out = self.run_cli("check", run_id)
        self.assertEqual(code, 0, out)
        code, out = self.run_cli(
            "review",
            run_id,
            "--decision",
            "approve",
            "--reviewer",
            "교수",
            "--note",
            "승인",
        )
        self.assertEqual(code, 0, out)
        code, out = self.run_cli("status", INQUIRY)
        self.assertIn("완료", out)

    def test_refusal_exit_code(self):
        code, out = self.run_cli("start", DIGEST, "--at", "2026-11-19T09:15:00+09:00")
        self.assertEqual(code, 1)
        self.assertIn("[거부]", out)


if __name__ == "__main__":
    unittest.main()
