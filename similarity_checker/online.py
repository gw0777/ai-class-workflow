"""온라인 학술 DB 질의(Crossref / OpenAlex / GitHub 코드 검색) — 기존 문헌 유무 검사.

모든 함수는 네트워크 실패 시 예외 대신 errors 목록에 사유를 담아 돌려준다.
"""
from __future__ import annotations

import difflib
import os
import re
import time
from typing import Any

CROSSREF_API = "https://api.crossref.org/works"
OPENALEX_API = "https://api.openalex.org/works"
GITHUB_API = "https://api.github.com"


def norm_title(t: str) -> str:
    t = re.sub(r"<[^>]+>", "", t or "")
    return re.sub(r"[^0-9a-z가-힣]+", "", t.lower())


def title_similarity(a: str, b: str) -> float:
    na, nb = norm_title(a), norm_title(b)
    if not na or not nb:
        return 0.0
    return round(difflib.SequenceMatcher(None, na, nb, autojunk=False).ratio(), 3)


class HttpClient:
    """requests 기반 얇은 클라이언트(테스트에서 교체 가능)."""

    def __init__(self, timeout: float = 15.0, user_agent: str | None = None, sleep: float = 0.0):
        self.timeout = timeout
        self.sleep = sleep
        mailto = os.environ.get("CROSSREF_MAILTO", "")
        default_ua = f"similarity-checker/0.1 (mailto:{mailto})" if mailto else "similarity-checker/0.1"
        self.user_agent = user_agent or default_ua

    def get_json(self, url: str, params: dict | None = None, headers: dict | None = None) -> Any:
        import requests  # 지연 import: 오프라인 사용 시 불필요

        h = {"User-Agent": self.user_agent, "Accept": "application/json"}
        if headers:
            h.update(headers)
        if self.sleep:
            time.sleep(self.sleep)
        r = requests.get(url, params=params, headers=h, timeout=self.timeout)
        r.raise_for_status()
        return r.json()


# --------------------------------------------------------------------------- #
# 제공자별 검색
# --------------------------------------------------------------------------- #
def crossref_search(query: str, client: HttpClient, rows: int = 5) -> list[dict]:
    params = {"query.bibliographic": query, "rows": rows}
    mailto = os.environ.get("CROSSREF_MAILTO")
    if mailto:
        params["mailto"] = mailto
    data = client.get_json(CROSSREF_API, params)
    out = []
    for it in data.get("message", {}).get("items", []):
        title = (it.get("title") or [""])[0]
        year = None
        for k in ("published-print", "published-online", "issued", "created"):
            dp = (it.get(k) or {}).get("date-parts") or [[None]]
            if dp and dp[0] and dp[0][0]:
                year = dp[0][0]
                break
        authors = ", ".join(f"{a.get('family','')} {a.get('given','')}".strip() for a in it.get("author", [])[:3])
        out.append({"provider": "crossref", "title": title, "doi": it.get("DOI"), "url": it.get("URL"),
                    "year": year, "authors": authors, "container": (it.get("container-title") or [""])[0]})
    return out


def crossref_doi(doi: str, client: HttpClient) -> dict | None:
    try:
        data = client.get_json(f"{CROSSREF_API}/{doi}")
    except Exception:
        return None
    it = data.get("message", {})
    if not it:
        return None
    return {"provider": "crossref", "title": (it.get("title") or [""])[0], "doi": it.get("DOI"), "url": it.get("URL")}


def openalex_search(query: str, client: HttpClient, rows: int = 5) -> list[dict]:
    params = {"search": query, "per-page": rows}
    mailto = os.environ.get("CROSSREF_MAILTO")
    if mailto:
        params["mailto"] = mailto
    data = client.get_json(OPENALEX_API, params)
    out = []
    for it in data.get("results", []):
        out.append({"provider": "openalex", "title": it.get("title") or it.get("display_name") or "",
                    "doi": (it.get("doi") or "").replace("https://doi.org/", "") or None,
                    "url": it.get("doi") or it.get("id"), "year": it.get("publication_year"),
                    "authors": ", ".join((a.get("author") or {}).get("display_name", "") for a in it.get("authorships", [])[:3])})
    return out


def github_code_search(phrase: str, client: HttpClient, token: str | None = None, rows: int = 5) -> list[dict]:
    """GitHub 코드 검색으로 문장이 공개 저장소에 존재하는지 확인(토큰 필요)."""
    token = token or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN 이 없어 GitHub 코드 검색을 건너뜁니다.")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    data = client.get_json(f"{GITHUB_API}/search/code", {"q": f'"{phrase}"', "per_page": rows}, headers)
    out = []
    for it in data.get("items", []):
        repo = (it.get("repository") or {}).get("full_name", "")
        out.append({"provider": "github", "title": f"{repo}/{it.get('path','')}", "url": it.get("html_url"), "score": 1.0})
    return out


# --------------------------------------------------------------------------- #
# 기존 문헌 유무
# --------------------------------------------------------------------------- #
def check_existence(title: str, sample_sentences: list[str] | None = None, client: HttpClient | None = None,
                    providers: tuple[str, ...] = ("crossref", "openalex"), min_score: float = 0.6,
                    github_phrases: int = 0) -> dict:
    """제목(및 선택적으로 대표 문장)으로 기존 문헌 존재 여부를 조회한다."""
    client = client or HttpClient()
    hits: list[dict] = []
    errors: list[str] = []
    fns = {"crossref": crossref_search, "openalex": openalex_search}
    for p in providers:
        fn = fns.get(p)
        if not fn:
            continue
        try:
            for it in fn(title, client):
                sc = title_similarity(title, it["title"])
                if sc >= min_score:
                    hits.append({**it, "score": sc})
        except Exception as e:
            errors.append(f"{p}: {e}")
    if github_phrases and sample_sentences:
        for s in sample_sentences[:github_phrases]:
            try:
                for it in github_code_search(s[:120], client):
                    hits.append({**it, "matched_sentence": s})
            except Exception as e:
                errors.append(f"github: {e}")
                break
    hits.sort(key=lambda h: -float(h.get("score", 0)))
    return {"title": title, "hits": hits, "errors": errors,
            "verdict": "기존 문헌과 제목 일치 가능성" if any(h.get("score", 0) >= 0.9 for h in hits) else ("유사 제목 존재" if hits else "유사 문헌 없음")}


def pick_sample_sentences(sentences: list[str], k: int = 3, min_len: int = 40) -> list[str]:
    """온라인 구문 검색용 대표 문장: 길고 숫자·기호가 적은 문장 우선."""
    cands = [s for s in sentences if len(s) >= min_len and sum(c.isdigit() for c in s) < 4]
    cands.sort(key=lambda s: -len(s))
    step = max(1, len(cands) // k) if cands else 1
    return cands[::step][:k]
