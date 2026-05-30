"""데이터 모델 정의 (Pydantic).

한국특수체육학회지 SEM 논문 자동생산 파이프라인에서 단계 간 주고받는
모든 데이터 구조를 정의한다.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Stage(str, Enum):
    """파이프라인 단계 식별자."""

    STAGE1_PARALLEL_SEARCH = "stage1_parallel_search"
    STAGE2_DEDUP_NORMALIZE = "stage2_dedup_normalize"
    STAGE3_RESEARCHER = "stage3_researcher"
    STAGE4_GENERATOR = "stage4_generator"
    STAGE5_PROOFREADER = "stage5_proofreader"
    STAGE6_EVALUATOR = "stage6_evaluator"
    STAGE7_FINALIZE = "stage7_finalize"


class Reference(BaseModel):
    """참고문헌 1건."""

    title: str = ""
    authors: str = ""
    year: str = ""
    source: str = ""
    url: str | None = None
    doi: str | None = None
    apa: str = ""  # 정규화된 APA 7th 인용 문자열
    verified: bool = False


class SearchResult(BaseModel):
    """Gemini 검색(학술/동향) 결과."""

    query: str
    summary: str = ""
    references: list[Reference] = Field(default_factory=list)
    citation_urls: list[str] = Field(default_factory=list)
    raw_text: str = ""


class ReferencePrecheck(BaseModel):
    """Claude 참고문헌 사전검증 결과."""

    assessment: str = ""
    risky_claims: list[str] = Field(default_factory=list)
    recommended_keywords: list[str] = Field(default_factory=list)


class Stage1Result(BaseModel):
    """Stage 1 (병렬 검색) 통합 결과."""

    academic: SearchResult
    trend: SearchResult
    precheck: ReferencePrecheck


class Stage2Result(BaseModel):
    """Stage 2 (중복제거 + 인용 정규화) 결과."""

    references: list[Reference] = Field(default_factory=list)
    reference_list_apa: list[str] = Field(default_factory=list)
    duplicates_removed: int = 0


class EvidenceStructure(BaseModel):
    """Stage 3 (Claude Researcher) 근거구조."""

    research_question: str = ""
    hypotheses: list[str] = Field(default_factory=list)
    latent_variables: list[str] = Field(default_factory=list)
    measurement_model: str = ""
    structural_model: str = ""
    argument_outline: str = ""
    raw: str = ""


class PaperDraft(BaseModel):
    """Stage 4 (Claude Generator) / Stage 5 교정 후 논문 초안."""

    title: str = ""
    abstract: str = ""
    body_markdown: str = ""
    iteration: int = 1


class ProofreadResult(BaseModel):
    """Stage 5 (Claude Proofreader) 7항목 교정 결과."""

    checklist: dict[str, str] = Field(default_factory=dict)
    corrected_markdown: str = ""
    notes: str = ""


class CriterionScore(BaseModel):
    """평가 항목 1건의 점수 (0~10)."""

    name: str
    score: float = 0.0
    comment: str = ""


class EvaluationResult(BaseModel):
    """Stage 6 (Claude Evaluator) 채점 결과."""

    scores: list[CriterionScore] = Field(default_factory=list)
    total: float = 0.0
    gate_threshold: float = 70.0
    passed: bool = False
    feedback: str = ""


class PipelineRequest(BaseModel):
    """파이프라인 실행 요청."""

    topic: str = Field(..., description="논문 주제")
    keywords: list[str] = Field(default_factory=list, description="핵심 키워드(선택)")
    max_iterations: int = Field(default=3, ge=1, le=10, description="GATE 미통과 시 Stage4 최대 재시도 횟수")
    gate_threshold: float = Field(default=70.0, ge=0, le=100, description="GATE 통과 총점 기준")


class StageTrace(BaseModel):
    """단계별 실행 추적 정보."""

    stage: str
    started_at: str = Field(default_factory=_now)
    finished_at: str | None = None
    ok: bool = True
    detail: str = ""


class PipelineResult(BaseModel):
    """파이프라인 전체 실행 결과."""

    topic: str
    stage1: Stage1Result | None = None
    stage2: Stage2Result | None = None
    evidence: EvidenceStructure | None = None
    final_paper: PaperDraft | None = None
    evaluation: EvaluationResult | None = None
    passed: bool = False
    iterations: int = 0
    saved_path: str | None = None
    trace: list[StageTrace] = Field(default_factory=list)
    started_at: str = Field(default_factory=_now)
    finished_at: str | None = None

    def to_public_dict(self) -> dict[str, Any]:
        """외부(REST/MCP)로 반환하기 좋은 dict 형태."""
        return self.model_dump(mode="json")
