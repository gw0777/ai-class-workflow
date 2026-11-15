"""유사도 비교 엔진: 코퍼스(1:N) 및 문서 간(1:1) 검사."""
from __future__ import annotations

import difflib
import os
from dataclasses import asdict, dataclass, field

from .config import CheckConfig
from .index import CorpusIndex
from .textproc import Sentence, prepare_sentences, shingles, text_sha256


@dataclass
class Match:
    kind: str                    # '일치' | '유사'
    source: str                  # 출처 라벨(파일 경로, github:..., 등)
    source_title: str
    source_doc_id: int
    source_sent_idx: int
    source_text: str
    matched_tokens: int          # min_run 이상 연속 일치 어절 합
    longest_run: int             # 가장 긴 연속 일치 어절 수
    ratio: float                 # 어절 시퀀스 유사도(0~1)
    blocks: list[tuple[int, int]] = field(default_factory=list)  # 검사문장 내 일치 구간 [(start, end)]


@dataclass
class SentenceReport:
    idx: int
    text: str
    n_tokens: int
    excluded: str | None = None
    match: Match | None = None

    @property
    def suspect(self) -> bool:
        return self.match is not None


@dataclass
class SourceSummary:
    source: str
    title: str
    doc_id: int
    n_sentences: int        # 이 출처와 일치/유사한 검사 문장 수
    suspect_tokens: int     # 그 문장들의 어절 수 합
    share_pct: float        # 검사 어절 대비 비율


@dataclass
class CheckResult:
    target: str
    title: str
    n_sentences: int
    n_checked: int
    n_excluded: int
    tokens_checked: int
    suspect_sentences: int
    suspect_tokens: int
    exact_tokens: int
    similarity_pct: float        # 표절률(의심문장 어절 / 검사 어절)
    exact_pct: float             # 정확일치율(연속일치 어절 / 검사 어절)
    sentence_pct: float          # 의심 문장 비율
    corpus_overlap_pct: float    # 문서 지문이 코퍼스에 이미 존재하는 비율(중복 문서 감지)
    sources: list[SourceSummary]
    sentences: list[SentenceReport]
    excluded_counts: dict
    config: dict
    corpus_stats: dict
    warnings: list[str] = field(default_factory=list)
    references: list | None = None     # references.verify_all 결과(선택)
    existence: dict | None = None      # online.check_existence 결과(선택)

    def to_dict(self) -> dict:
        return asdict(self)


def grade(pct: float) -> str:
    """카피킬러식 등급 해석(참고용)."""
    if pct < 5:
        return "안전"
    if pct < 15:
        return "주의"
    if pct < 30:
        return "경고"
    return "위험"


def _align(a: list[str], b: list[str], min_run: int, char_floor: float = 0.45) -> tuple[int, int, float, list[tuple[int, int]]]:
    """어절 시퀀스 정렬. ratio 는 어절 단위 유사도와 글자 단위 유사도 중 큰 값(교착어 변형에 관대)."""
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    blocks = [bl for bl in sm.get_matching_blocks() if bl.size > 0]
    runs = [bl for bl in blocks if bl.size >= min_run]
    matched = sum(bl.size for bl in runs)
    longest = max((bl.size for bl in blocks), default=0)
    ratio = sm.ratio()
    if ratio >= char_floor:  # 어절 유사도가 어느 정도 있을 때만 글자 단위 재계산(비용 절감)
        ca, cb = "".join(a), "".join(b)
        if abs(len(ca) - len(cb)) <= max(len(ca), len(cb)) * 0.5:
            ratio = max(ratio, difflib.SequenceMatcher(None, ca, cb, autojunk=False).ratio())
    spans = [(bl.a, bl.a + bl.size) for bl in runs]
    return matched, longest, ratio, spans


def best_match_for(sent: Sentence, index: CorpusIndex, cfg: CheckConfig, exclude_doc_ids: set[int]) -> Match | None:
    hs = shingles(sent.ltokens, index.ngram)
    cands = index.candidates(hs, cfg.candidates, exclude_doc_ids)
    best: Match | None = None
    for sid, _hits in cands:
        row = index.sentence(sid)
        if not row:
            continue
        if any(p and p in row["source"] for p in cfg.exclude_sources):
            continue
        b = row["ltokens"].split()
        matched, longest, ratio, spans = _align(sent.ltokens, b, cfg.min_run)
        if matched >= cfg.min_run:
            kind = "일치"
        elif ratio >= cfg.sim_threshold:
            kind = "유사"
        else:
            continue
        m = Match(kind, row["source"], row["title"] or "", row["doc_id"], row["idx"], row["text"],
                  matched, longest, round(ratio, 3), spans)
        if best is None or (m.matched_tokens, m.ratio) > (best.matched_tokens, best.ratio):
            best = m
    return best


def check_text(text: str, index: CorpusIndex, cfg: CheckConfig, target: str = "", title: str = "",
               exclude_self: bool = True) -> CheckResult:
    sents, _refs = prepare_sentences(text, cfg)
    exclude_ids: set[int] = set()
    warnings: list[str] = list(index.warnings)
    if exclude_self:
        same = index.find_by_sha(text_sha256(text))
        if same:
            exclude_ids.add(same.id)
            warnings.append(f"코퍼스에 동일 문서(id={same.id}, {same.source})가 있어 비교에서 제외했습니다.")
        if target:
            by_src = index.find_by_source(os.path.abspath(target)) or index.find_by_source(target)
            if by_src:
                exclude_ids.add(by_src.id)

    all_hashes: set[int] = set()
    reports: list[SentenceReport] = []
    excluded_counts: dict[str, int] = {}
    tokens_checked = suspect_tokens = exact_tokens = suspect_sentences = 0
    per_source: dict[int, SourceSummary] = {}

    for s in sents:
        rep = SentenceReport(idx=s.idx, text=s.text, n_tokens=s.n_tokens, excluded=s.excluded)
        if s.excluded:
            excluded_counts[s.excluded] = excluded_counts.get(s.excluded, 0) + 1
            reports.append(rep)
            continue
        tokens_checked += s.n_tokens
        all_hashes |= shingles(s.ltokens, index.ngram)
        m = best_match_for(s, index, cfg, exclude_ids)
        if m:
            rep.match = m
            suspect_sentences += 1
            suspect_tokens += s.n_tokens
            exact_tokens += min(m.matched_tokens, s.n_tokens)
            ss = per_source.get(m.source_doc_id)
            if ss is None:
                ss = per_source[m.source_doc_id] = SourceSummary(m.source, m.source_title, m.source_doc_id, 0, 0, 0.0)
            ss.n_sentences += 1
            ss.suspect_tokens += s.n_tokens
        reports.append(rep)

    n_checked = sum(1 for s in sents if not s.excluded)
    denom = tokens_checked or 1
    for ss in per_source.values():
        ss.share_pct = round(100 * ss.suspect_tokens / denom, 1)
    sources = sorted(per_source.values(), key=lambda x: -x.suspect_tokens)
    overlap = index.overlap_ratio(all_hashes) if all_hashes and not exclude_ids else 0.0

    return CheckResult(
        target=target, title=title, n_sentences=len(sents), n_checked=n_checked,
        n_excluded=len(sents) - n_checked, tokens_checked=tokens_checked,
        suspect_sentences=suspect_sentences, suspect_tokens=suspect_tokens, exact_tokens=exact_tokens,
        similarity_pct=round(100 * suspect_tokens / denom, 1),
        exact_pct=round(100 * exact_tokens / denom, 1),
        sentence_pct=round(100 * suspect_sentences / (n_checked or 1), 1),
        corpus_overlap_pct=round(100 * overlap, 1),
        sources=sources, sentences=reports, excluded_counts=excluded_counts,
        config=cfg.to_dict(), corpus_stats=index.stats(), warnings=warnings,
    )


def compare_texts(text_a: str, text_b: str, cfg: CheckConfig, label_a: str = "A", label_b: str = "B",
                  title_a: str = "", title_b: str = "") -> CheckResult:
    """1:1 비교 — B를 임시 코퍼스로 만들어 A를 검사한다."""
    idx = CorpusIndex(":memory:", ngram=cfg.index_ngram)
    idx.add_text(text_b, source=label_b, title=title_b or label_b, kind="compare", cfg=cfg)
    res = check_text(text_a, idx, cfg, target=label_a, title=title_a or label_a, exclude_self=False)
    idx.close()
    return res
