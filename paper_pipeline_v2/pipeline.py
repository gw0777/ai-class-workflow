"""파이프라인 로직.

한국특수체육학회지 SEM 논문 자동생산 시스템의 핵심 7단계 로직과
Gemini / Claude 클라이언트를 정의한다.

설계 요점
--------
- Stage 1은 asyncio.gather()로 세 작업을 "동시" 실행한다.
    Gemini 학술검색 || Gemini 동향검색 || Claude 참고문헌 사전검증
- Claude 호출은 공식 anthropic SDK(AsyncAnthropic)를 사용한다.
    모델: claude-opus-4-8 / adaptive thinking / 프롬프트 캐싱 / 스트리밍.
- Gemini 호출은 REST(generateContent)를 httpx로 직접 호출하며
    google_search grounding을 켜서 본문 + 출처 URL을 얻는다.
- GATE(기본 70점) 통과 시 결과 저장, 미통과 시 Stage 4로 회귀(재생성).
"""
from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from anthropic import AsyncAnthropic
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from models import (
    CriterionScore,
    EvaluationResult,
    EvidenceStructure,
    PaperDraft,
    PipelineRequest,
    PipelineResult,
    ProofreadResult,
    Reference,
    ReferencePrecheck,
    SearchResult,
    Stage,
    Stage1Result,
    Stage2Result,
    StageTrace,
)


# --------------------------------------------------------------------------- #
# 설정
# --------------------------------------------------------------------------- #
class Settings(BaseSettings):
    """환경변수 기반 설정.

    .env 또는 OS 환경변수에서 읽는다. (대소문자 무관)
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gemini_api_key: str = ""
    claude_api_key: str = ""

    claude_model: str = "claude-opus-4-8"
    gemini_model: str = "gemini-2.5-flash"

    claude_effort: str = "high"  # low | medium | high | xhigh | max
    output_dir: str = "output"

    gemini_timeout: float = 120.0
    claude_timeout: float = 600.0


settings = Settings()


# --------------------------------------------------------------------------- #
# 공용 헬퍼
# --------------------------------------------------------------------------- #
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def loads_json(text: str) -> Any:
    """LLM 응답 문자열에서 JSON 객체/배열을 최대한 견고하게 추출한다."""
    if not text:
        return None
    cleaned = text.strip()
    # ```json ... ``` 펜스 제거
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # 본문 어딘가의 첫 { ... } 또는 [ ... ] 블록 시도
    for opener, closer in (("{", "}"), ("[", "]")):
        start = cleaned.find(opener)
        end = cleaned.rfind(closer)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                continue
    return None


_P_VALUE_RE = re.compile(r"([pP]\s*[<>=]\s*)0(\.\d+)")


def normalize_p_values(text: str) -> str:
    """APA 규칙: p값의 선행 0 제거. 예) p = 0.03 -> p = .03, p < 0.001 -> p < .001"""
    return _P_VALUE_RE.sub(r"\1\2", text or "")


def _norm_key(ref: Reference) -> str:
    """중복 판별용 정규화 키 (DOI > URL > 제목)."""
    if ref.doi:
        return "doi:" + re.sub(r"\s+", "", ref.doi.lower())
    if ref.url:
        return "url:" + ref.url.strip().lower().rstrip("/")
    return "title:" + re.sub(r"[^a-z0-9가-힣]", "", (ref.title or "").lower())


def dedup_references(refs: list[Reference]) -> tuple[list[Reference], int]:
    """참고문헌 중복 제거. (유지목록, 제거건수) 반환."""
    seen: dict[str, Reference] = {}
    removed = 0
    for ref in refs:
        key = _norm_key(ref)
        if not key or key in ("title:",):
            continue
        if key in seen:
            removed += 1
            # 더 풍부한 정보를 가진 쪽으로 병합
            existing = seen[key]
            if len(ref.apa) > len(existing.apa):
                existing.apa = ref.apa
            existing.verified = existing.verified or ref.verified
            continue
        seen[key] = ref
    return list(seen.values()), removed


# --------------------------------------------------------------------------- #
# Gemini 클라이언트 (REST + google_search grounding)
# --------------------------------------------------------------------------- #
class GeminiClient:
    """Gemini generateContent 호출 래퍼.

    google_search 도구를 켜서 grounding(출처) 메타데이터를 함께 받는다.
    """

    BASE = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model

    async def search(self, prompt: str) -> SearchResult:
        """프롬프트로 검색/생성하고 본문 + 출처 URL을 추출한다."""
        url = f"{self.BASE}/{self.model}:generateContent"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}],
        }
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=settings.gemini_timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return self._parse(prompt, data)

    @staticmethod
    def _parse(query: str, data: dict[str, Any]) -> SearchResult:
        candidates = data.get("candidates") or []
        text = ""
        urls: list[str] = []
        if candidates:
            cand = candidates[0]
            parts = (cand.get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts)
            chunks = (cand.get("groundingMetadata") or {}).get("groundingChunks") or []
            for c in chunks:
                uri = (c.get("web") or {}).get("uri")
                if uri:
                    urls.append(uri)
        # 중복 URL 제거(순서 유지)
        urls = list(dict.fromkeys(urls))
        return SearchResult(query=query, summary=text, raw_text=text, citation_urls=urls)


# --------------------------------------------------------------------------- #
# Claude 클라이언트 (anthropic 공식 SDK)
# --------------------------------------------------------------------------- #
class ClaudeClient:
    """Claude 호출 래퍼.

    - adaptive thinking + effort 파라미터.
    - 안정적인 시스템 프롬프트는 프롬프트 캐싱(ephemeral)으로 비용 절감.
    - 긴 출력 타임아웃을 피하려고 항상 스트리밍으로 받는다.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.client = AsyncAnthropic(
            api_key=api_key or settings.claude_api_key or None,
            timeout=settings.claude_timeout,
        )
        self.model = model or settings.claude_model

    async def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 8000,
        effort: str | None = None,
    ) -> str:
        """system/user 프롬프트로 1회 호출하고 텍스트를 반환한다."""
        system_blocks = [
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }
        ]
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            output_config={"effort": effort or settings.claude_effort},
            system=system_blocks,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            message = await stream.get_final_message()
        return "".join(b.text for b in message.content if b.type == "text").strip()

    async def complete_json(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 8000,
        effort: str | None = None,
    ) -> Any:
        """complete() 후 JSON을 파싱해 반환한다."""
        text = await self.complete(system, user, max_tokens=max_tokens, effort=effort)
        return loads_json(text)


# --------------------------------------------------------------------------- #
# 파이프라인 본체
# --------------------------------------------------------------------------- #
class PaperPipeline:
    """SEM 논문 자동생산 7단계 파이프라인."""

    def __init__(
        self,
        gemini: GeminiClient | None = None,
        claude: ClaudeClient | None = None,
    ) -> None:
        self.gemini = gemini or GeminiClient()
        self.claude = claude or ClaudeClient()

    # ----- Stage 1: 병렬 검색 + 사전검증 ---------------------------------- #
    async def stage1_parallel_search(
        self, topic: str, keywords: list[str] | None = None
    ) -> Stage1Result:
        """Gemini 학술검색 || Gemini 동향검색 || Claude 참고문헌 사전검증."""
        kw = ", ".join(keywords or []) or "(키워드 미지정)"

        academic_prompt = (
            f"당신은 특수체육(adapted physical activity) 분야 학술 사서입니다.\n"
            f"주제: '{topic}' (키워드: {kw})\n"
            f"이 주제와 관련된 최근 5~10년 핵심 학술 논문/이론을 한국어로 정리하세요. "
            f"가능하면 저자, 연도, 출처(학술지)를 포함하고, 신뢰할 수 있는 출처 링크를 제시하세요."
        )
        trend_prompt = (
            f"당신은 특수체육 정책/현장 동향 분석가입니다.\n"
            f"주제: '{topic}' (키워드: {kw})\n"
            f"최신 정책, 현장 적용 사례, 사회적 동향을 한국어로 정리하고 출처 링크를 제시하세요."
        )

        precheck_system = (
            "당신은 한국특수체육학회지(SEM 논문) 심사 경험이 풍부한 방법론 전문가입니다. "
            "제시된 주제에 대해 참고문헌 인용 시 주의할 점을 사전 검증합니다. "
            "반드시 아래 JSON 스키마로만 답하세요.\n"
            '{"assessment": "<주제의 인용/근거 환경에 대한 총평>", '
            '"risky_claims": ["<과대해석·근거부족 위험이 있는 주장>", ...], '
            '"recommended_keywords": ["<추가로 검색하면 좋은 학술 키워드>", ...]}'
        )
        precheck_user = f"주제: {topic}\n키워드: {kw}\n위 JSON 스키마로만 답하세요."

        academic_task = self.gemini.search(academic_prompt)
        trend_task = self.gemini.search(trend_prompt)
        precheck_task = self.claude.complete_json(
            precheck_system, precheck_user, max_tokens=2000
        )

        academic, trend, precheck_raw = await asyncio.gather(
            academic_task, trend_task, precheck_task
        )

        precheck = self._coerce_precheck(precheck_raw)
        # Gemini 결과의 grounding URL을 참고문헌 후보로 변환
        academic.references = self._urls_to_refs(academic.citation_urls)
        trend.references = self._urls_to_refs(trend.citation_urls)
        return Stage1Result(academic=academic, trend=trend, precheck=precheck)

    @staticmethod
    def _coerce_precheck(raw: Any) -> ReferencePrecheck:
        if isinstance(raw, dict):
            return ReferencePrecheck(
                assessment=str(raw.get("assessment", "")),
                risky_claims=[str(x) for x in raw.get("risky_claims", []) or []],
                recommended_keywords=[
                    str(x) for x in raw.get("recommended_keywords", []) or []
                ],
            )
        return ReferencePrecheck(assessment=str(raw or ""))

    @staticmethod
    def _urls_to_refs(urls: list[str]) -> list[Reference]:
        return [Reference(title=u, url=u, source="web") for u in urls]

    # ----- Stage 2: 중복제거 + 인용 정규화 -------------------------------- #
    async def stage2_dedup_normalize(self, stage1: Stage1Result) -> Stage2Result:
        """참고문헌 병합 -> 중복제거 -> APA 7th 인용 정규화."""
        merged = list(stage1.academic.references) + list(stage1.trend.references)
        deduped, removed = dedup_references(merged)

        system = (
            "당신은 APA 7th 인용 전문가입니다. 제시된 참고문헌 후보 목록을 "
            "APA 7판 형식의 참고문헌 문자열로 정규화합니다. 정보가 부족하면 "
            "가능한 범위에서 정리하되 사실을 지어내지 마세요. "
            "반드시 아래 JSON 배열로만 답하세요.\n"
            '[{"index": 0, "apa": "<APA 7th 형식 문자열>"}, ...]'
        )
        candidate_text = json.dumps(
            [
                {"index": i, "title": r.title, "url": r.url, "source": r.source}
                for i, r in enumerate(deduped)
            ],
            ensure_ascii=False,
        )
        apa_list: list[str] = []
        if deduped:
            raw = await self.claude.complete_json(
                system, candidate_text, max_tokens=4000
            )
            if isinstance(raw, list):
                for item in raw:
                    if not isinstance(item, dict):
                        continue
                    idx = item.get("index")
                    apa = str(item.get("apa", "")).strip()
                    if isinstance(idx, int) and 0 <= idx < len(deduped) and apa:
                        deduped[idx].apa = apa
            apa_list = [r.apa for r in deduped if r.apa]

        return Stage2Result(
            references=deduped,
            reference_list_apa=apa_list,
            duplicates_removed=removed,
        )

    # ----- Stage 3: Claude Researcher (근거구조) -------------------------- #
    async def stage3_researcher(
        self, topic: str, stage1: Stage1Result, stage2: Stage2Result
    ) -> EvidenceStructure:
        system = (
            "당신은 한국특수체육학회지에 게재되는 구조방정식모형(SEM) 논문의 "
            "연구설계 전문가(Researcher)입니다. 주어진 검색 요약과 참고문헌을 바탕으로 "
            "근거구조(연구문제, 가설, 7개 잠재변수, 측정모형, 구조모형, 논거 개요)를 설계합니다. "
            "반드시 아래 JSON 스키마로만 답하세요.\n"
            "{"
            '"research_question": "<연구문제>", '
            '"hypotheses": ["H1 ...", "H2 ..."], '
            '"latent_variables": ["<잠재변수1>", ... 정확히 7개], '
            '"measurement_model": "<측정모형 설명: 각 잠재변수의 관측변수>", '
            '"structural_model": "<구조모형: 잠재변수 간 경로>", '
            '"argument_outline": "<서론-이론-방법-결과-논의로 이어지는 논거 개요>"'
            "}"
        )
        ctx = (
            f"[주제]\n{topic}\n\n"
            f"[학술검색 요약]\n{stage1.academic.summary[:4000]}\n\n"
            f"[동향검색 요약]\n{stage1.trend.summary[:2000]}\n\n"
            f"[사전검증 총평]\n{stage1.precheck.assessment}\n"
            f"[주의 주장]\n- " + "\n- ".join(stage1.precheck.risky_claims) + "\n\n"
            f"[참고문헌 수]\n{len(stage2.references)}건\n\n"
            "위 JSON 스키마로만 답하세요. latent_variables는 반드시 7개."
        )
        raw = await self.claude.complete_json(system, ctx, max_tokens=6000)
        if isinstance(raw, dict):
            return EvidenceStructure(
                research_question=str(raw.get("research_question", "")),
                hypotheses=[str(x) for x in raw.get("hypotheses", []) or []],
                latent_variables=[str(x) for x in raw.get("latent_variables", []) or []],
                measurement_model=str(raw.get("measurement_model", "")),
                structural_model=str(raw.get("structural_model", "")),
                argument_outline=str(raw.get("argument_outline", "")),
                raw=json.dumps(raw, ensure_ascii=False),
            )
        return EvidenceStructure(raw=str(raw or ""))

    # ----- Stage 4: Claude Generator (SEM 논문 초안) --------------------- #
    async def stage4_generator(
        self,
        topic: str,
        evidence: EvidenceStructure,
        stage2: Stage2Result,
        *,
        iteration: int = 1,
        feedback: str = "",
    ) -> PaperDraft:
        system = (
            "당신은 한국특수체육학회지(Korean Journal of Adapted Physical Activity) 게재 수준의 "
            "구조방정식모형(SEM) 논문을 작성하는 전문 연구자(Generator)입니다.\n"
            "엄수 규칙:\n"
            "1) 표본 크기는 N=274 로 일관되게 보고한다.\n"
            "2) 잠재변수는 정확히 7개를 사용한다.\n"
            "3) 모든 p값은 선행 0을 제거한다. (예: p = .03, p < .001)\n"
            "4) 모든 표(Table)의 제목/캡션은 표 좌상단(left-top)에 APA 7th 형식으로 배치한다.\n"
            "5) 적합도 지수(χ², df, CFI, TLI, RMSEA, SRMR)를 결과에 보고한다.\n"
            "6) 구성: 국문초록 -> 서론 -> 이론적 배경 -> 연구방법 -> 연구결과 -> 논의 및 결론 -> 참고문헌.\n"
            "7) 학술적 한국어 문체(APA 7판)를 사용한다. 사실을 날조하지 말고 제공된 근거구조를 따른다.\n"
            "출력은 Markdown 한 편의 완결된 논문으로 작성한다."
        )
        refs = "\n".join(f"- {a}" for a in stage2.reference_list_apa[:40])
        revision = (
            f"\n\n[이전 평가 피드백 — 이번 개정에서 반드시 반영]\n{feedback}\n"
            if feedback
            else ""
        )
        user = (
            f"[주제]\n{topic}\n\n"
            f"[연구문제]\n{evidence.research_question}\n\n"
            f"[가설]\n" + "\n".join(evidence.hypotheses) + "\n\n"
            f"[7개 잠재변수]\n" + ", ".join(evidence.latent_variables) + "\n\n"
            f"[측정모형]\n{evidence.measurement_model}\n\n"
            f"[구조모형]\n{evidence.structural_model}\n\n"
            f"[논거 개요]\n{evidence.argument_outline}\n\n"
            f"[참고문헌(APA)]\n{refs}\n"
            f"{revision}\n"
            "위 내용을 바탕으로 N=274, 7잠재변수 SEM 논문 한 편을 Markdown으로 작성하세요."
        )
        body = await self.claude.complete(system, user, max_tokens=32000)
        body = normalize_p_values(body)
        title = self._extract_title(body) or f"{topic}: 구조방정식모형 분석"
        abstract = self._extract_abstract(body)
        return PaperDraft(
            title=title, abstract=abstract, body_markdown=body, iteration=iteration
        )

    @staticmethod
    def _extract_title(md: str) -> str:
        for line in md.splitlines():
            s = line.strip()
            if s.startswith("#"):
                return s.lstrip("#").strip()
        return ""

    @staticmethod
    def _extract_abstract(md: str) -> str:
        m = re.search(r"(?:국문\s*)?초록\s*\n+(.+?)(?:\n#{1,6}\s|\n\*\*|\Z)", md, re.DOTALL)
        return m.group(1).strip()[:1500] if m else ""

    # ----- Stage 5: Claude Proofreader (7항목 교정) ---------------------- #
    async def stage5_proofreader(self, draft: PaperDraft) -> ProofreadResult:
        system = (
            "당신은 한국특수체육학회지 교정 전문가(Proofreader)입니다. "
            "아래 7개 항목을 점검하고 본문을 교정합니다.\n"
            "1. 표본(N=274) 일관성  2. 잠재변수 7개 일치  3. p값 선행 0 제거\n"
            "4. 표 캡션 좌상단/APA 형식  5. 적합도 지수 보고 완전성\n"
            "6. APA 7th 인용/참고문헌 형식  7. 학술적 문체/오탈자\n"
            "반드시 아래 JSON 스키마로만 답하세요.\n"
            "{"
            '"checklist": {"1_sample":"OK/수정내용", "2_latent":"...", "3_pvalue":"...", '
            '"4_table":"...", "5_fit":"...", "6_apa":"...", "7_style":"..."}, '
            '"corrected_markdown": "<교정된 전체 Markdown 논문>", '
            '"notes": "<요약 코멘트>"'
            "}"
        )
        raw = await self.claude.complete_json(
            system, draft.body_markdown, max_tokens=32000
        )
        if isinstance(raw, dict) and raw.get("corrected_markdown"):
            checklist = raw.get("checklist") or {}
            return ProofreadResult(
                checklist={str(k): str(v) for k, v in checklist.items()},
                corrected_markdown=normalize_p_values(str(raw["corrected_markdown"])),
                notes=str(raw.get("notes", "")),
            )
        # 파싱 실패 시 원본 유지
        return ProofreadResult(
            checklist={"_warning": "교정 JSON 파싱 실패 — 원본 유지"},
            corrected_markdown=draft.body_markdown,
        )

    # ----- Stage 6: Claude Evaluator (0~10 채점, GATE) ------------------- #
    EVAL_CRITERIA = [
        "이론적 배경/문헌 적절성",
        "연구문제·가설 명료성",
        "측정모형 타당성(7잠재변수)",
        "구조모형 적합도 보고(CFI/TLI/RMSEA/SRMR)",
        "표본·표집 적절성(N=274)",
        "통계 보고 정확성(APA·p값 선행0)",
        "결과 해석 타당성",
        "논의·시사점",
        "학술적 글쓰기/형식(APA 7th)",
        "윤리·연구의 제한점",
    ]

    async def stage6_evaluator(
        self, markdown: str, gate_threshold: float = 70.0
    ) -> EvaluationResult:
        criteria_list = "\n".join(f"{i+1}. {c}" for i, c in enumerate(self.EVAL_CRITERIA))
        system = (
            "당신은 한국특수체육학회지 편집위원(Evaluator)입니다. "
            "다음 10개 항목을 각각 0~10점으로 엄정하게 채점합니다(총점 100).\n"
            f"{criteria_list}\n\n"
            "반드시 아래 JSON 스키마로만 답하세요.\n"
            "{"
            '"scores": [{"name":"<항목명>", "score": <0~10>, "comment":"<근거>"}, ... 10개], '
            '"feedback": "<총평 및 개선 지시(다음 개정에 반영할 구체 사항)>"'
            "}"
        )
        raw = await self.claude.complete_json(system, markdown, max_tokens=6000)
        scores: list[CriterionScore] = []
        feedback = ""
        if isinstance(raw, dict):
            for item in raw.get("scores", []) or []:
                if isinstance(item, dict):
                    try:
                        sc = float(item.get("score", 0))
                    except (TypeError, ValueError):
                        sc = 0.0
                    scores.append(
                        CriterionScore(
                            name=str(item.get("name", "")),
                            score=max(0.0, min(10.0, sc)),
                            comment=str(item.get("comment", "")),
                        )
                    )
            feedback = str(raw.get("feedback", ""))
        total = round(sum(s.score for s in scores), 2)
        return EvaluationResult(
            scores=scores,
            total=total,
            gate_threshold=gate_threshold,
            passed=total >= gate_threshold,
            feedback=feedback,
        )

    # ----- Stage 7: 저장 ------------------------------------------------- #
    def stage7_finalize(self, result: PipelineResult) -> str:
        """GATE 통과 결과를 파일로 저장하고 경로를 반환한다."""
        out_dir = Path(settings.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r"[^0-9A-Za-z가-힣]+", "_", result.topic)[:40] or "paper"
        base = out_dir / f"{stamp}_{slug}"

        if result.final_paper:
            base.with_suffix(".md").write_text(
                result.final_paper.body_markdown, encoding="utf-8"
            )
        base.with_suffix(".json").write_text(
            json.dumps(result.to_public_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return str(base.with_suffix(".md"))

    # ----- 전체 실행 (GATE 회귀 루프 포함) ------------------------------- #
    async def run(self, request: PipelineRequest) -> PipelineResult:
        result = PipelineResult(topic=request.topic)

        async def _step(stage: Stage, coro):
            tr = StageTrace(stage=stage.value)
            try:
                value = await coro
                tr.finished_at = _now()
                result.trace.append(tr)
                return value
            except Exception as exc:  # noqa: BLE001 - 추적에 기록 후 재전파
                tr.ok = False
                tr.detail = f"{type(exc).__name__}: {exc}"
                tr.finished_at = _now()
                result.trace.append(tr)
                raise

        # Stage 1~3
        result.stage1 = await _step(
            Stage.STAGE1_PARALLEL_SEARCH,
            self.stage1_parallel_search(request.topic, request.keywords),
        )
        result.stage2 = await _step(
            Stage.STAGE2_DEDUP_NORMALIZE,
            self.stage2_dedup_normalize(result.stage1),
        )
        result.evidence = await _step(
            Stage.STAGE3_RESEARCHER,
            self.stage3_researcher(request.topic, result.stage1, result.stage2),
        )

        # Stage 4~6 (+7 회귀 루프)
        feedback = ""
        last_eval: EvaluationResult | None = None
        last_paper: PaperDraft | None = None
        for i in range(1, request.max_iterations + 1):
            result.iterations = i
            draft = await _step(
                Stage.STAGE4_GENERATOR,
                self.stage4_generator(
                    request.topic,
                    result.evidence,
                    result.stage2,
                    iteration=i,
                    feedback=feedback,
                ),
            )
            proof = await _step(
                Stage.STAGE5_PROOFREADER, self.stage5_proofreader(draft)
            )
            paper = PaperDraft(
                title=draft.title,
                abstract=draft.abstract,
                body_markdown=proof.corrected_markdown,
                iteration=i,
            )
            evaluation = await _step(
                Stage.STAGE6_EVALUATOR,
                self.stage6_evaluator(paper.body_markdown, request.gate_threshold),
            )
            last_paper, last_eval = paper, evaluation
            if evaluation.passed:
                break
            feedback = evaluation.feedback  # GATE 미통과 -> Stage 4로 회귀

        result.final_paper = last_paper
        result.evaluation = last_eval
        result.passed = bool(last_eval and last_eval.passed)

        # Stage 7: 통과 시에만 저장
        if result.passed:
            result.saved_path = self.stage7_finalize(result)
        result.finished_at = _now()
        return result


# 단독 실행용 간이 진입점
async def _demo() -> None:  # pragma: no cover
    pipeline = PaperPipeline()
    res = await pipeline.run(
        PipelineRequest(topic="지적장애 학생의 신체활동 참여와 삶의 질", max_iterations=2)
    )
    print(json.dumps(res.to_public_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(_demo())
