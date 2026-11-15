import os
import tempfile

from similarity_checker.compare import check_text, compare_texts, grade
from similarity_checker.config import CheckConfig
from similarity_checker.index import CorpusIndex

SOURCE = """스포츠교육학 기초 이론
인간의 신체 활동과 스포츠를 교육의 관점에서 심층적으로 탐구하는 학문 분야이다.
협동학습은 학생들이 소집단을 이루어 공동의 목표를 달성하기 위해 서로 돕는 수업 모형이다.
교사는 촉진자 역할을 수행하며 학생들은 상호의존적으로 과제를 해결한다.
자기결정성 이론은 자율성, 유능성, 관계성의 세 가지 기본 심리 욕구를 가정한다.
"""

QUERY = """협동학습 적용 연구
인간의 신체 활동과 스포츠를 교육의 관점에서 심층적으로 탐구하는 학문 분야가 스포츠교육학이다.
협동학습이란 학생들이 소집단을 이루어서 공동의 목표를 달성하려고 서로 돕는 수업 모형을 말한다.
이 문장은 완전히 독창적으로 작성되어 어떤 문헌과도 겹치지 않는 새로운 서술이다.
선행연구는 협동학습이 또래 수용도를 높인다고 보고하였다(김철수, 2020).
"""


def _index(cfg=None):
    idx = CorpusIndex(":memory:")
    idx.add_text(SOURCE, source="src.txt", title="스포츠교육학 기초 이론", cfg=cfg or CheckConfig())
    return idx


def test_exact_and_paraphrase_detection():
    cfg = CheckConfig()
    res = check_text(QUERY, _index(cfg), cfg, target="q.txt", title="질의")
    kinds = {r.idx: (r.match.kind if r.match else None) for r in res.sentences}
    # 0: 제목(짧은문장 제외), 1: 그대로 복사 → 일치, 2: 조사 바꿔쓰기 → 일치/유사, 3: 독창 → None, 4: 출처표시 → 제외
    assert res.sentences[0].excluded == "짧은문장"
    assert kinds[1] == "일치"
    assert kinds[2] in ("일치", "유사")
    assert kinds[3] is None
    assert res.sentences[4].excluded == "출처표시"
    assert res.suspect_sentences == 2 and res.n_checked == 3
    assert 50 < res.similarity_pct < 80
    assert res.sources[0].source == "src.txt" and res.sources[0].n_sentences == 2
    assert res.sentences[1].match.longest_run >= 6
    assert res.sentences[1].match.blocks  # 하이라이트 구간


def test_strict_mode_is_less_tolerant_than_loose():
    loose = check_text(QUERY, _index(), CheckConfig(loose=True), target="q")
    strict_cfg = CheckConfig(loose=False)
    idx = CorpusIndex(":memory:")
    idx.add_text(SOURCE, source="src.txt", cfg=strict_cfg)
    strict = check_text(QUERY, idx, strict_cfg, target="q")
    assert strict.exact_tokens <= loose.exact_tokens


def test_min_run_controls_exact_match():
    cfg = CheckConfig(min_run=20, sim_threshold=0.99)
    res = check_text(QUERY, _index(cfg), cfg, target="q")
    assert res.suspect_sentences == 0 and res.similarity_pct == 0.0


def test_self_document_is_excluded_by_sha():
    cfg = CheckConfig()
    idx = _index(cfg)
    idx.add_text(QUERY, source="q.txt", cfg=cfg)
    res = check_text(QUERY, idx, cfg, target="q.txt")
    assert any("동일 문서" in w for w in res.warnings)
    assert all((r.match is None or r.match.source != "q.txt") for r in res.sentences)


def test_exclude_sources_substring():
    cfg = CheckConfig(exclude_sources=["src"])
    res = check_text(QUERY, _index(cfg), cfg, target="q")
    assert res.suspect_sentences == 0


def test_compare_one_to_one():
    res = compare_texts(QUERY, SOURCE, CheckConfig(), label_a="A", label_b="B")
    assert res.suspect_sentences == 2
    assert res.sources[0].source == "B"


def test_index_persistence_and_duplicate_handling():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "c.db")
        idx = CorpusIndex(path)
        rec, st = idx.add_text(SOURCE, source="a.txt", title="A")
        assert st == "added"
        _, st2 = idx.add_text(SOURCE, source="a.txt", title="A")
        assert st2 == "skipped-duplicate"
        _, st3 = idx.add_text(SOURCE, source="b.txt", title="B")   # 같은 내용 다른 이름
        assert st3 == "skipped-duplicate"
        _, st4 = idx.add_text(SOURCE + "\n추가된 문장이 있다.", source="a.txt", title="A2")
        assert st4 == "added" and idx.get(idx.list()[0].id).title == "A2"
        idx.close()
        idx2 = CorpusIndex(path)
        assert idx2.stats()["documents"] == 1
        assert idx2.search_title("A2")[0][0].title == "A2"
        assert idx2.remove(idx2.list()[0].id) and idx2.stats()["documents"] == 0
        idx2.close()


def test_grade_bands():
    assert grade(0) == "안전" and grade(10) == "주의" and grade(20) == "경고" and grade(50) == "위험"
