"""순수 함수 단위 테스트 (네트워크/API 키 불필요).

실행:
    cd paper_pipeline_v2 && python -m pytest -q
    또는
    cd paper_pipeline_v2 && python tests/test_helpers.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Reference  # noqa: E402
from pipeline import dedup_references, normalize_p_values  # noqa: E402


def test_normalize_p_values_basic():
    assert normalize_p_values("p = 0.03") == "p = .03"
    assert normalize_p_values("p < 0.001") == "p < .001"
    assert normalize_p_values("p > 0.05") == "p > .05"


def test_normalize_p_values_keeps_non_p_numbers():
    # p값이 아닌 일반 수치의 선행 0은 유지되어야 한다
    text = "신뢰구간은 0.45였다."
    assert normalize_p_values(text) == text


def test_normalize_p_values_inline():
    assert normalize_p_values("(β = .31, p = 0.012)") == "(β = .31, p = .012)"


def test_dedup_by_doi():
    refs = [
        Reference(title="A", doi="10.1/x"),
        Reference(title="A dup", doi="10.1/X"),  # 대소문자 차이 -> 동일 취급
        Reference(title="B", doi="10.2/y"),
    ]
    out, removed = dedup_references(refs)
    assert removed == 1
    assert len(out) == 2


def test_dedup_by_url():
    refs = [
        Reference(title="A", url="https://e.com/x/"),
        Reference(title="A2", url="https://e.com/x"),  # 끝 슬래시 차이 -> 동일
        Reference(title="C", url="https://e.com/z"),
    ]
    out, removed = dedup_references(refs)
    assert removed == 1
    assert len(out) == 2


def test_dedup_keeps_richer_apa():
    refs = [
        Reference(title="A", doi="10.1/x", apa="짧음"),
        Reference(title="A", doi="10.1/x", apa="훨씬 더 긴 APA 인용 문자열입니다"),
    ]
    out, removed = dedup_references(refs)
    assert removed == 1
    assert out[0].apa == "훨씬 더 긴 APA 인용 문자열입니다"


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
        print(f"  ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} passed")


if __name__ == "__main__":
    _run_all()
