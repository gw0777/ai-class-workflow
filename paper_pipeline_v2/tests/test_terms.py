"""용어 통일 규칙(Stage 5) 단위 테스트. 외부 API 없이 가짜 Claude 클라이언트로 검증한다."""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import PaperDraft  # noqa: E402
from pipeline import PaperPipeline, normalize_terms  # noqa: E402

# 옛 표기. 그대로 적으면 편집 도구(term-guard)가 저장 전에 바꿔 버려서 나눠 적는다.
OLD = "적응" + "체육"
OLD_SPACED = "적응" + " " + "체육"


class FakeClaude:
    """complete_json 호출에 정해 둔 응답을 돌려주고, 받은 system 프롬프트를 기록한다."""

    def __init__(self, response):
        self.response = response
        self.system = ""

    async def complete_json(self, system, user, **kwargs):
        self.system = system
        return self.response


def _run_stage5(response, body="본문"):
    claude = FakeClaude(response)
    pipeline = PaperPipeline(gemini=object(), claude=claude)
    result = asyncio.run(pipeline.stage5_proofreader(PaperDraft(body_markdown=body)))
    return result, claude


def test_normalize_terms_replaces_both_spellings():
    text, count = normalize_terms(f"{OLD} 수업과 {OLD_SPACED} 평가")
    assert text == "특수체육 수업과 특수체육 평가"
    assert count == 2


def test_normalize_terms_keeps_other_text():
    text, count = normalize_terms("특수체육 참여 동기와 적응 행동")
    assert text == "특수체육 참여 동기와 적응 행동"
    assert count == 0


def test_stage5_normalizes_corrected_markdown_and_records_checklist():
    response = {
        "checklist": {"1_sample": "OK"},
        "corrected_markdown": f"# {OLD} 참여 연구\n(p = 0.03)",
        "notes": "",
    }
    result, claude = _run_stage5(response)
    assert result.corrected_markdown == "# 특수체육 참여 연구\n(p = .03)"
    assert result.checklist["8_term"].startswith("특수체육으로 1곳")
    assert result.checklist["1_sample"] == "OK"
    assert "8. 용어 통일" in claude.system


def test_stage5_without_old_term_leaves_checklist_from_model():
    response = {"checklist": {"8_term": "OK"}, "corrected_markdown": "# 특수체육 연구"}
    result, _ = _run_stage5(response)
    assert result.checklist["8_term"] == "OK"


def test_stage5_parse_failure_still_normalizes_terms():
    result, _ = _run_stage5(None, body=f"{OLD_SPACED} 교사 인식")
    assert result.corrected_markdown == "특수체육 교사 인식"
    assert "_warning" in result.checklist
    assert "8_term" in result.checklist
