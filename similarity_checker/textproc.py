"""텍스트 전처리: 정규화, 한국어 문장 분리, 어절 토큰화, n-gram 지문, 제외 규칙."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Iterable

HANGUL = "가-힣"
_WS_RE = re.compile(r"[ \t 　]+")
_TOKEN_CLEAN_RE = re.compile(rf"[^0-9a-z{HANGUL}]+")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?。？！])(?<!\.\.)(?<!\d\.)(?<![A-Z]\.)\s+")
_HANGUL_SYL_RE = re.compile(rf"[{HANGUL}]")

# 흔한 조사/어미(loose 비교용). 긴 것부터 매칭되도록 정렬.
_PARTICLES = sorted(
    [
        "으로부터", "에서는", "에게서", "으로는", "으로서", "으로써", "에서", "에게", "까지", "부터",
        "처럼", "보다", "조차", "마저", "이나", "이며", "이다", "였다", "하고", "에는", "과는",
        "이란", "이라", "에서도", "으로도", "에게는", "으로", "한다", "하는", "하여", "해서",
        "와는", "은", "는", "이", "가", "을", "를", "의", "에", "로", "과", "와", "도", "만", "나",
    ],
    key=len,
    reverse=True,
)
_PARTICLE_RE = re.compile("(" + "|".join(_PARTICLES) + ")$")

_REF_HEADING_RE = re.compile(
    r"^\s*(?:\d+[.\s]*|[IVX]+[.\s]*|[【\[]?)?\s*(참\s*고\s*문\s*헌|인\s*용\s*문\s*헌|References?|REFERENCES|Bibliography|BIBLIOGRAPHY|Works Cited)\s*[】\]]?\s*[:：]?\s*$"
)
_TOC_LINE_RE = re.compile(r"(\.{3,}|…{2,}|·{3,})\s*\d+\s*$")
_CITATION_RE = re.compile(
    r"\((?:[^()]*?)(?:19|20)\d{2}[a-z]?(?:[^()]*?)\)"   # (김철수, 2020) / (Smith et al., 2019)
    r"|\[\d{1,3}(?:\s*[,，–-]\s*\d{1,3})*\]"              # [1], [2-4]
    r"|\bet\s+al\.?"                                      # et al.
    r"|[가-힣A-Za-z]{2,}\s*\((?:19|20)\d{2}\)"            # 김철수(2020)
)
TOKENIZER_VERSION = 2   # 토큰화/조사 규칙이 바뀌면 올린다(코퍼스 재색인 필요 여부 판단)
MAX_MERGE_CHARS = 300   # 이 길이를 넘으면 줄 병합을 멈춘다(슬라이드형 PDF 보호)
MAX_SENT_WORDS = 40     # 이 어절 수를 넘는 '문장'은 균등 분할

_QUOTE_PAIRS = [("“", "”"), ('"', '"'), ("‘", "’"), ("「", "」"), ("『", "』"), ("'", "'")]


# --------------------------------------------------------------------------- #
# 정규화
# --------------------------------------------------------------------------- #
def fix_spaced_hangul(text: str) -> str:
    """'스 포 츠 교 육 학' 처럼 글자마다 공백이 들어간 PDF 추출물을 복원한다.

    줄 단위로 한 글자짜리 한글 토큰 비율이 40% 이상이면 한글 사이의 1칸 공백을 제거하고,
    2칸 이상 공백은 어절 경계로 본다.
    """
    out = []
    for line in text.splitlines():
        toks = line.split()
        if len(toks) >= 4:
            single = sum(1 for t in toks if len(t) == 1 and _HANGUL_SYL_RE.fullmatch(t))
            if single / len(toks) >= 0.4:
                tmp = re.sub(r" {2,}", "\x00", line)
                tmp = re.sub(rf"(?<=[{HANGUL}]) (?=[{HANGUL}])", "", tmp)
                line = tmp.replace("\x00", " ")
        out.append(line)
    return "\n".join(out)


def normalize_text(text: str) -> str:
    """제어문자 제거, 공백 통일, 하이픈 줄바꿈 복원."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\u0000-\u0008\u000b\u000c\u000e-\u001f-]", " ", text)
    text = re.sub(r"(?<=[A-Za-z])-\n(?=[a-z])", "", text)  # hyphen-\nation
    lines = [_WS_RE.sub(" ", ln).strip() for ln in text.split("\n")]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# 문장 분리
# --------------------------------------------------------------------------- #
def _merge_wrapped_lines(block: str) -> list[str]:
    """PDF 줄바꿈으로 끊긴 문장을 다시 잇는다. 짧은 줄(제목·글머리)은 그대로 둔다."""
    merged: list[str] = []
    buf = ""
    for ln in block.split("\n"):
        ln = ln.strip()
        if not ln:
            continue
        if buf:
            ends = buf[-1] in ".!?。？！:：”\"’」』"
            if not ends and 25 <= len(buf) <= MAX_MERGE_CHARS and not _TOC_LINE_RE.search(buf):
                buf = buf + " " + ln
                continue
            merged.append(buf)
        buf = ln
    if buf:
        merged.append(buf)
    return merged


def _chunk_long(sentence: str, max_words: int = MAX_SENT_WORDS) -> list[str]:
    """마침표 없이 길게 이어진 텍스트(슬라이드·표)는 어절 수 기준으로 균등 분할한다."""
    words = sentence.split()
    if len(words) <= max_words:
        return [sentence]
    n_chunks = -(-len(words) // max_words)
    size = -(-len(words) // n_chunks)
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)]


def split_sentences(text: str) -> list[str]:
    """한국어/영어 혼합 텍스트를 문장 단위로 나눈다."""
    text = normalize_text(text)
    sents: list[str] = []
    for block in re.split(r"\n\s*\n", text):
        for line in _merge_wrapped_lines(block):
            for s in _SENT_SPLIT_RE.split(line):
                s = s.strip()
                if s:
                    sents.extend(_chunk_long(s))
    return sents


# --------------------------------------------------------------------------- #
# 토큰화 / 지문
# --------------------------------------------------------------------------- #
def tokenize(text: str) -> list[str]:
    """어절 단위 토큰(소문자, 구두점 제거)."""
    toks = []
    for raw in text.lower().split():
        t = _TOKEN_CLEAN_RE.sub("", raw)
        if t:
            toks.append(t)
    return toks


def strip_particle(token: str) -> str:
    """끝에 붙은 흔한 조사/어미를 제거(2글자 이상 남을 때만)."""
    if len(token) < 3 or not _HANGUL_SYL_RE.search(token[-1]):
        return token
    m = _PARTICLE_RE.search(token)
    if m and len(token) - len(m.group(1)) >= 2:
        return token[: -len(m.group(1))]
    return token


def loose_tokens(tokens: Iterable[str]) -> list[str]:
    return [strip_particle(t) for t in tokens]


def shingle_hash(tokens: list[str]) -> int:
    """어절 n-gram → 64bit 부호 있는 정수(SQLite INTEGER)."""
    h = hashlib.blake2b(" ".join(tokens).encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(h, "big", signed=True)


def shingles(tokens: list[str], n: int) -> set[int]:
    if len(tokens) < n:
        return {shingle_hash(tokens)} if tokens else set()
    return {shingle_hash(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


# --------------------------------------------------------------------------- #
# 섹션 / 제외 규칙
# --------------------------------------------------------------------------- #
def find_reference_section(text: str) -> tuple[str, str]:
    """본문과 참고문헌 목록을 나눈다. (본문, 참고문헌부) — 없으면 참고문헌부는 ''.

    문서 앞쪽 30% 이전의 '참고문헌' 표제(목차 등)는 무시한다.
    """
    lines = normalize_text(text).split("\n")
    n = len(lines)
    for i in range(n - 1, int(n * 0.3) - 1, -1):
        if _REF_HEADING_RE.match(lines[i]):
            return "\n".join(lines[:i]), "\n".join(lines[i + 1 :])
    return "\n".join(lines), ""


def is_quote_sentence(s: str) -> bool:
    st = s.strip()
    for a, b in _QUOTE_PAIRS:
        if st.startswith(a) and st.endswith(b) and len(st) > 2:
            return True
        # 문장 대부분이 인용부호 안에 있는 경우
        m = re.search(re.escape(a) + r"(.{10,})" + re.escape(b), st)
        if m and len(m.group(1)) >= 0.6 * len(st):
            return True
    return False


def has_citation(s: str) -> bool:
    return bool(_CITATION_RE.search(s))


def is_toc_line(s: str) -> bool:
    return bool(_TOC_LINE_RE.search(s.strip()))


def digit_ratio(s: str) -> float:
    alnum = [c for c in s if c.isalnum()]
    if not alnum:
        return 0.0
    return sum(c.isdigit() for c in alnum) / len(alnum)


@dataclass
class Sentence:
    idx: int
    text: str
    tokens: list[str] = field(default_factory=list)
    ltokens: list[str] = field(default_factory=list)   # loose tokens
    excluded: str | None = None                        # 제외 사유(None이면 검사 대상)

    @property
    def n_tokens(self) -> int:
        return len(self.tokens)


def prepare_sentences(text: str, cfg) -> tuple[list[Sentence], str]:
    """문장 목록(제외 사유 포함)과 참고문헌부 텍스트를 돌려준다."""
    body, refs = find_reference_section(text)
    if not cfg.exclude_references:
        body = text
        refs = refs  # 파싱용으로는 그대로 유지
    out: list[Sentence] = []
    for i, s in enumerate(split_sentences(body)):
        toks = tokenize(s)
        sent = Sentence(idx=i, text=s, tokens=toks, ltokens=loose_tokens(toks) if cfg.loose else list(toks))
        if cfg.exclude_toc and is_toc_line(s):
            sent.excluded = "목차"
        elif len(toks) < cfg.min_tokens:
            sent.excluded = "짧은문장"
        elif digit_ratio(s) > 0.5:
            sent.excluded = "숫자/표"
        elif cfg.exclude_quotes and is_quote_sentence(s):
            sent.excluded = "인용문"
        elif cfg.exclude_citations and has_citation(s):
            sent.excluded = "출처표시"
        out.append(sent)
    return out, refs


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
