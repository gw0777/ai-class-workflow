"""메인 MCP 서버 + n8n 연동용 REST API.

구성
----
- MCP(Model Context Protocol) 서버: 각 Stage(1~7)와 전체 실행을 MCP tool로 노출.
    MCP Streamable HTTP 엔드포인트는 `/mcp` 에 마운트된다.
- FastAPI REST API: n8n의 HTTP Request 노드가 호출할 수 있는 엔드포인트.
    `/api/...` 경로.

실행
----
    uvicorn mcp_server:app --host 0.0.0.0 --port 8000
또는
    python mcp_server.py
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from mcp.server.fastmcp import FastMCP

from models import (
    EvidenceStructure,
    PipelineRequest,
    Stage1Result,
    Stage2Result,
)
from pipeline import PaperPipeline, settings

pipeline = PaperPipeline()

# --------------------------------------------------------------------------- #
# MCP 서버 정의 — 각 Stage를 도구로 노출
# --------------------------------------------------------------------------- #
mcp = FastMCP("paper-pipeline-v2")


@mcp.tool()
async def stage1_parallel_search(topic: str, keywords: list[str] | None = None) -> dict[str, Any]:
    """Stage 1 (병렬): Gemini 학술검색 || Gemini 동향검색 || Claude 참고문헌 사전검증."""
    result = await pipeline.stage1_parallel_search(topic, keywords or [])
    return result.model_dump(mode="json")


@mcp.tool()
async def stage2_dedup_normalize(stage1: dict[str, Any]) -> dict[str, Any]:
    """Stage 2: 참고문헌 중복제거 + APA 7th 인용 정규화. (입력: stage1 결과 dict)"""
    result = await pipeline.stage2_dedup_normalize(Stage1Result.model_validate(stage1))
    return result.model_dump(mode="json")


@mcp.tool()
async def stage3_researcher(
    topic: str, stage1: dict[str, Any], stage2: dict[str, Any]
) -> dict[str, Any]:
    """Stage 3: Claude Researcher — 근거구조(연구문제/가설/7잠재변수/측정·구조모형) 설계."""
    result = await pipeline.stage3_researcher(
        topic,
        Stage1Result.model_validate(stage1),
        Stage2Result.model_validate(stage2),
    )
    return result.model_dump(mode="json")


@mcp.tool()
async def stage4_generator(
    topic: str,
    evidence: dict[str, Any],
    stage2: dict[str, Any],
    iteration: int = 1,
    feedback: str = "",
) -> dict[str, Any]:
    """Stage 4: Claude Generator — SEM 논문 초안(N=274, 7잠재변수, p값 선행0 제거, APA 표)."""
    result = await pipeline.stage4_generator(
        topic,
        EvidenceStructure.model_validate(evidence),
        Stage2Result.model_validate(stage2),
        iteration=iteration,
        feedback=feedback,
    )
    return result.model_dump(mode="json")


@mcp.tool()
async def stage5_proofreader(markdown: str) -> dict[str, Any]:
    """Stage 5: Claude Proofreader — 7항목 교정."""
    from models import PaperDraft

    result = await pipeline.stage5_proofreader(PaperDraft(body_markdown=markdown))
    return result.model_dump(mode="json")


@mcp.tool()
async def stage6_evaluator(markdown: str, gate_threshold: float = 70.0) -> dict[str, Any]:
    """Stage 6: Claude Evaluator — 10항목 0~10점 채점, 총점 70+ 시 GATE 통과."""
    result = await pipeline.stage6_evaluator(markdown, gate_threshold)
    return result.model_dump(mode="json")


@mcp.tool()
async def run_full_pipeline(
    topic: str,
    keywords: list[str] | None = None,
    max_iterations: int = 3,
    gate_threshold: float = 70.0,
) -> dict[str, Any]:
    """전체 7단계 파이프라인 실행. GATE 통과 시 결과 저장, 미통과 시 Stage4 회귀."""
    req = PipelineRequest(
        topic=topic,
        keywords=keywords or [],
        max_iterations=max_iterations,
        gate_threshold=gate_threshold,
    )
    result = await pipeline.run(req)
    return result.to_public_dict()


# --------------------------------------------------------------------------- #
# FastAPI 앱 — MCP 마운트 + n8n용 REST
# --------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    # MCP Streamable HTTP 세션 매니저 구동
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="논문생산 무인 파이프라인 v2",
    description="한국특수체육학회지 SEM 논문 자동생산 시스템 (FastAPI + MCP SDK)",
    version="2.0.0",
    lifespan=lifespan,
)

# MCP 엔드포인트 마운트: http(s)://host:8000/mcp
app.mount("/mcp", mcp.streamable_http_app())


@app.get("/health")
async def health() -> dict[str, Any]:
    """헬스체크 + 키 설정 여부(값은 노출하지 않음)."""
    return {
        "status": "ok",
        "claude_model": settings.claude_model,
        "gemini_model": settings.gemini_model,
        "gemini_key_set": bool(settings.gemini_api_key),
        "claude_key_set": bool(settings.claude_api_key or os.getenv("ANTHROPIC_API_KEY")),
    }


@app.post("/api/pipeline/run")
async def api_run(request: PipelineRequest) -> dict[str, Any]:
    """전체 파이프라인 실행 (n8n HTTP Request 노드용 메인 엔드포인트)."""
    try:
        result = await pipeline.run(request)
        return result.to_public_dict()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}") from exc


@app.post("/api/stage1")
async def api_stage1(payload: dict[str, Any]) -> dict[str, Any]:
    """Stage 1 단독 실행. body: {\"topic\": str, \"keywords\": [str]}"""
    topic = payload.get("topic")
    if not topic:
        raise HTTPException(status_code=422, detail="'topic' is required")
    result = await pipeline.stage1_parallel_search(topic, payload.get("keywords") or [])
    return result.model_dump(mode="json")


@app.post("/api/stage2")
async def api_stage2(payload: dict[str, Any]) -> dict[str, Any]:
    """Stage 2 단독 실행. body: {\"stage1\": {...}}"""
    result = await pipeline.stage2_dedup_normalize(
        Stage1Result.model_validate(payload["stage1"])
    )
    return result.model_dump(mode="json")


@app.post("/api/stage3")
async def api_stage3(payload: dict[str, Any]) -> dict[str, Any]:
    """Stage 3 단독 실행. body: {\"topic\": str, \"stage1\": {...}, \"stage2\": {...}}"""
    result = await pipeline.stage3_researcher(
        payload["topic"],
        Stage1Result.model_validate(payload["stage1"]),
        Stage2Result.model_validate(payload["stage2"]),
    )
    return result.model_dump(mode="json")


@app.post("/api/stage4")
async def api_stage4(payload: dict[str, Any]) -> dict[str, Any]:
    """Stage 4 단독 실행. body: {\"topic\", \"evidence\", \"stage2\", \"iteration\", \"feedback\"}"""
    result = await pipeline.stage4_generator(
        payload["topic"],
        EvidenceStructure.model_validate(payload["evidence"]),
        Stage2Result.model_validate(payload["stage2"]),
        iteration=int(payload.get("iteration", 1)),
        feedback=payload.get("feedback", ""),
    )
    return result.model_dump(mode="json")


@app.post("/api/stage5")
async def api_stage5(payload: dict[str, Any]) -> dict[str, Any]:
    """Stage 5 단독 실행. body: {\"markdown\": str}"""
    from models import PaperDraft

    result = await pipeline.stage5_proofreader(
        PaperDraft(body_markdown=payload["markdown"])
    )
    return result.model_dump(mode="json")


@app.post("/api/stage6")
async def api_stage6(payload: dict[str, Any]) -> dict[str, Any]:
    """Stage 6 단독 실행. body: {\"markdown\": str, \"gate_threshold\": float}"""
    result = await pipeline.stage6_evaluator(
        payload["markdown"], float(payload.get("gate_threshold", 70.0))
    )
    return result.model_dump(mode="json")


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "mcp_server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
