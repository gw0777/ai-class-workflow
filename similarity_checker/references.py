"""참고문헌 목록 파싱 + 실존 여부 검증."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .online import HttpClient, crossref_doi, crossref_search, openalex_search, title_similarity
from .textproc import find_reference_section, normalize_text

_DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>)\]]+)")
_YEAR_RE = re.compile(r"\(((?:19|20)\d{2})[a-z]?(?:,[^)]*)?\)|\b((?:19|20)\d{2})[a-z]?\b")
_URL_RE = re.compile(r"https?://\S+")
_ENTRY_START_RE = re.compile(
    r"^\s*(?:\[\d{1,3}\]|\d{1,3}[.)])\s*"                            # [1] / 1. / 1)
    r"|^\s*[A-Z][A-Za-z'’\-]+,\s*[A-Z]"                               # Smith, J.
    r"|^\s*[가-힣]{2,5}(?:\s*[,·]\s*[가-힣]{2,5})*\s*[\(,(]"            # 김철수(2020) / 김철수, 이영희(
    r"|^\s*[가-힣]{2,5}\s*(?:외|등)\s*[\(,]"                            # 김철수 외(2020)
)


@dataclass
class Reference:
    raw: str
    authors: str = ""
    year: str = ""
    title: str = ""
    doi: str | None = None
    url: str | None = None
    status: str = ""          # 확인 | 의심 | 미확인 | 오프라인
    note: str = ""
    matched_title: str = ""
    score: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def split_entries(section: str) -> list[str]:
    """참고문헌부 텍스트를 항목별로 나눈다(연속 줄 병합)."""
    entries: list[str] = []
    buf = ""
    for ln in normalize_text(section).split("\n"):
        ln = ln.strip()
        if not ln:
            continue
        if _ENTRY_START_RE.match(ln) and (not buf or _YEAR_RE.search(buf)):
            if buf:
                entries.append(buf)
            buf = ln
        else:
            buf = (buf + " " + ln).strip() if buf else ln
    if buf:
        entries.append(buf)
    return [e for e in entries if len(e) > 15]


def parse_reference(raw: str) -> Reference:
    ref = Reference(raw=raw)
    m = _DOI_RE.search(raw)
    if m:
        ref.doi = m.group(1).rstrip(".,;")
    u = _URL_RE.search(raw)
    if u and "doi.org" not in u.group(0):
        ref.url = u.group(0).rstrip(".,;")
    body = re.sub(r"^\s*(?:\[\d{1,3}\]|\d{1,3}[.)])\s*", "", raw)
    ym = _YEAR_RE.search(body)
    if ym:
        ref.year = ym.group(1) or ym.group(2)
        ref.authors = body[: ym.start()].strip(" ,.(")
        rest = body[ym.end():].lstrip(" ).")
        # 제목: 연도 뒤 첫 문장(마침표 또는 '. ' 까지). 한국어 제목에는 마침표가 드물다.
        tm = re.match(r"(.+?)(?:\.\s|\.$|,\s(?=[가-힣A-Z]))", rest + " ")
        ref.title = (tm.group(1) if tm else rest).strip(" .\"“”")
    else:
        ref.authors = body.split(".")[0].strip()
        ref.title = body
    if len(ref.title) > 200:
        ref.title = ref.title[:200]
    return ref


def extract_references(text: str) -> list[Reference]:
    _body, section = find_reference_section(text)
    if not section:
        return []
    return [parse_reference(e) for e in split_entries(section)]


def verify_reference(ref: Reference, client: HttpClient, ok: float = 0.85, maybe: float = 0.6) -> Reference:
    """Crossref(DOI → 서지검색) → OpenAlex 순으로 실존 확인."""
    # 1) DOI가 있으면 직접 조회
    if ref.doi:
        hit = crossref_doi(ref.doi, client)
        if hit:
            sc = title_similarity(ref.title, hit["title"]) if ref.title else 1.0
            ref.matched_title, ref.score = hit["title"], sc
            if sc >= maybe or not ref.title:
                ref.status, ref.note = "확인", "DOI 조회 성공"
            else:
                ref.status, ref.note = "의심", "DOI는 존재하나 제목 불일치"
            return ref
        ref.note = "DOI 조회 실패; "
    # 2) 서지 검색
    query = ref.title if len(ref.title) >= 10 else ref.raw
    best: dict | None = None
    errors = []
    for name, fn in (("crossref", crossref_search), ("openalex", openalex_search)):
        try:
            for it in fn(query, client, rows=5):
                sc = title_similarity(ref.title or ref.raw, it["title"])
                if ref.year and it.get("year") and abs(int(it["year"]) - int(ref.year)) > 1:
                    sc -= 0.1  # 연도 불일치 감점
                if best is None or sc > best["score"]:
                    best = {**it, "score": round(sc, 3)}
        except Exception as e:
            errors.append(f"{name}: {e}")
        if best and best["score"] >= ok:
            break
    if best is None:
        ref.status = "오프라인" if errors else "미확인"
        ref.note += "; ".join(errors) if errors else "학술 DB에서 찾지 못함(국내 학술지는 Crossref 미등재일 수 있음)"
        return ref
    ref.matched_title, ref.score = best["title"], best["score"]
    ref.doi = ref.doi or best.get("doi")
    ref.url = ref.url or best.get("url")
    if best["score"] >= ok:
        ref.status, ref.note = "확인", f"{best['provider']} 제목 일치({best['score']})"
    elif best["score"] >= maybe:
        ref.status, ref.note = "의심", f"{best['provider']} 제목 부분 일치({best['score']}) — 서지사항 확인 필요"
    else:
        ref.status, ref.note = "미확인", f"가장 가까운 결과 유사도 {best['score']} (국내 학술지/학위논문은 RISS·KCI에서 수동 확인)"
        ref.doi = None if not _DOI_RE.search(ref.raw) else ref.doi
    return ref


def verify_all(refs: list[Reference], client: HttpClient | None = None, online: bool = True) -> list[dict]:
    client = client or HttpClient(sleep=0.2)
    out = []
    for r in refs:
        if online:
            try:
                verify_reference(r, client)
            except Exception as e:  # 개별 실패가 전체를 막지 않도록
                r.status, r.note = "오프라인", str(e)
        else:
            r.status, r.note = "오프라인", "온라인 검증 생략(--online 미지정)"
        out.append(r.to_dict())
    return out


def summarize(results: list[dict]) -> dict:
    c = {"확인": 0, "의심": 0, "미확인": 0, "오프라인": 0}
    for r in results:
        c[r.get("status", "오프라인")] = c.get(r.get("status", "오프라인"), 0) + 1
    return {"total": len(results), **c}
