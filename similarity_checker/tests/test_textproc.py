from similarity_checker import textproc as tp
from similarity_checker.config import CheckConfig


def test_fix_spaced_hangul_restores_words():
    assert tp.fix_spaced_hangul("스 포 츠 교 육 학  기 초  이 론") == "스포츠교육학 기초 이론"
    # 정상 문장은 건드리지 않는다
    s = "협동학습은 학생들이 소집단을 이루어 학습한다"
    assert tp.fix_spaced_hangul(s) == s


def test_split_sentences_korean_and_decimal():
    text = "협동학습은 수업 모형이다. 효과는 p = 0.05 수준에서 유의하였다. 끝!"
    assert tp.split_sentences(text) == ["협동학습은 수업 모형이다.", "효과는 p = 0.05 수준에서 유의하였다.", "끝!"]


def test_split_sentences_merges_wrapped_lines_but_keeps_headings():
    text = "1. 서론\n협동학습은 학생들이 소집단을 이루어 공동의 목표를 달성하는\n수업 모형이다.\n\n2. 방법"
    sents = tp.split_sentences(text)
    assert sents == ["1. 서론", "협동학습은 학생들이 소집단을 이루어 공동의 목표를 달성하는 수업 모형이다.", "2. 방법"]


def test_long_unpunctuated_text_is_chunked():
    words = " ".join(f"어절{i}" for i in range(100))
    sents = tp.split_sentences(words)
    assert len(sents) == 3
    assert all(len(s.split()) <= tp.MAX_SENT_WORDS for s in sents)
    assert " ".join(sents) == words


def test_tokenize_and_loose():
    toks = tp.tokenize("협동학습은 학생들이 (소집단을) 이루어, 공동의 목표를!")
    assert toks == ["협동학습은", "학생들이", "소집단을", "이루어", "공동의", "목표를"]
    assert tp.loose_tokens(toks) == ["협동학습", "학생들", "소집단", "이루어", "공동", "목표"]
    assert tp.strip_particle("이") == "이"       # 너무 짧으면 유지
    assert tp.strip_particle("학교에서는") == "학교"


def test_shingles_are_stable_and_overlap():
    a = tp.shingles(["a", "b", "c", "d"], 3)
    b = tp.shingles(["x", "b", "c", "d"], 3)
    assert len(a) == 2 and len(a & b) == 1
    assert tp.shingles(["a"], 3) == {tp.shingle_hash(["a"])}


def test_reference_section_split():
    text = "서론 본문입니다.\n본문 둘째 줄.\n본문 셋째 줄.\n참고문헌\n김철수(2020). 제목. 학술지."
    body, refs = tp.find_reference_section(text)
    assert "참고문헌" not in body and refs.startswith("김철수")
    body2, refs2 = tp.find_reference_section("참고문헌\n앞쪽에 있는 표제는 무시\n본문\n본문\n본문\n본문\n본문")
    assert refs2 == ""


def test_exclusion_rules():
    cfg = CheckConfig()
    text = "\n".join([
        "제1장 서론 ........ 3",
        "“이것은 인용된 문장이며 열 어절이 넘도록 충분히 길게 작성되었다”",
        "선행연구는 효과를 보고하였다 (김철수, 2020) 그리고 더 있다.",
        "짧다.",
        "이 문장은 아무 제외 사유가 없는 보통의 검사 대상 문장이다.",
        "1 2 3 4 5 6 7 8 9 10 11 12",
    ])
    sents, _ = tp.prepare_sentences(text, cfg)
    reasons = [s.excluded for s in sents]
    assert reasons == ["목차", "인용문", "출처표시", "짧은문장", None, "숫자/표"]


def test_exclusion_can_be_disabled():
    cfg = CheckConfig(exclude_quotes=False, exclude_citations=False, exclude_toc=False, min_tokens=1)
    sents, _ = tp.prepare_sentences("“인용 문장 하나 둘 셋 넷 다섯 여섯”\n결과는 유의하였다 (이영희, 2019) 하였다 정말로.", cfg)
    assert [s.excluded for s in sents] == [None, None]
