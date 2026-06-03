"""메인 MCP 서버 + n8n 연동용 REST API + 구독 SaaS 수익화 인프라.

구성
----
- MCP(Model Context Protocol) 서버: 각 Stage(1~7)와 전체 실행을 MCP tool로 노출. `/mcp` 마운트.
- FastAPI REST API: n8n HTTP Request 노드가 호출. `/api/...`.
- 수익화: API 키 인증 + 테넌트별 사용량 미터링 + 월간 한도(Free 3편/월, Pro 무제한)
    + Stripe 웹훅/체크아웃 + 비동기 작업큐 + /api/plans, /api/usage, /api/signup.

실행
----
    uvicorn mcp_server:app --host 0.0.0.0 --port 8000
또는
    python mcp_server.py
"""
from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from mcp.server.fastmcp import FastMCP

import billing
import jobs
from models import (
    EvidenceStructure,
    PipelineRequest,
    Stage1Result,
    Stage2Result,
)
from pipeline import PaperPipeline, settings

pipeline = PaperPipeline()

# 수익화 토글: 기본 활성. 끄면 인증/한도 없이 동작(개발용).
BILLING_ENABLED = os.getenv("BILLING_ENABLED", "true").lower() in ("1", "true", "yes")
# 데모/셌프호스트 편의를 위한 공개 가입(키 발급) 허용 여부.
SIGNUP_OPEN = os.getenv("SIGNUP_OPEN", "true").lower() in ("1", "true", "yes")

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
# FastAPI 앱 — MCP 마운트 + REST + 수익화
# --------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    billing.init_db()
    jobs.init_db()
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="논문생산 파이프라인 v2 (구독 SaaS)",
    description="한국특수체육학회지 SEM 논문 자동생산 + 구독 기반 수익화 (FastAPI + MCP SDK)",
    version="2.2.0",
    lifespan=lifespan,
)

app.mount("/mcp", mcp.streamable_http_app())


# ----- 사용량 추적 미들웨어 (per-user API call counting) -------------------- #
@app.middleware("http")
async def usage_counter(request: Request, call_next):
    response = await call_next(request)
    try:
        if BILLING_ENABLED and request.url.path.startswith("/api/"):
            api_key = request.headers.get("x-api-key")
            if api_key:
                user = billing.get_user_by_api_key(api_key)
                if user:
                    billing.record_api_call(user["id"], request.url.path, response.status_code)
    except Exception:  # noqa: BLE001 - 미터링 실패가 요청을 막지 않도록
        pass
    return response


# ----- 인증 의존성 ---------------------------------------------------------- #
async def current_user(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> dict[str, Any]:
    if not BILLING_ENABLED:
        return {"id": 0, "email": "billing-disabled", "plan": "enterprise"}
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="X-API-Key 헤더가 필요합니다. POST /api/signup 으로 키를 발급받으세요.",
        )
    user = billing.get_user_by_api_key(x_api_key)
    if not user:
        raise HTTPException(status_code=401, detail="유효하지 않은 API 키입니다.")
    return user


# ----- 공개 엔드포인트 ------------------------------------------------------ #
@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": "2.2.0",
        "billing_enabled": BILLING_ENABLED,
        "claude_model": settings.claude_model,
        "gemini_model": settings.gemini_model,
        "gemini_key_set": bool(settings.gemini_api_key),
        "claude_key_set": bool(settings.claude_api_key or os.getenv("ANTHROPIC_API_KEY")),
    }


@app.get("/api/plans")
async def api_plans() -> dict[str, Any]:
    """구독 플랜 카탈로그(공개)."""
    return {"plans": billing.PLANS, "currency": "USD", "billing_period": "month"}


@app.post("/api/signup")
async def api_signup(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """API 키 발급(데모/셌프호스트). body: {\"email\": \"...\"} (선택)."""
    if not SIGNUP_OPEN:
        raise HTTPException(status_code=403, detail="공개 가입이 비활성화되어 있습니다.")
    email = (payload or {}).get("email")
    user = billing.create_user(email=email)
    return {
        "message": "API 키가 발급되었습니다. X-API-Key 헤더로 사용하세요.",
        "api_key": user["api_key"],
        "plan": user["plan"],
        "quota": billing.quota_status(user["id"]),
    }


# ----- 인증 필요 엔드포인트 ------------------------------------------------- #
@app.get("/api/usage")
async def api_usage(user: dict = Depends(current_user)) -> dict[str, Any]:
    """현재 사용자의 플랜/사용량/잔여 한도 + 최근 이력."""
    if user["id"] == 0:  # billing 비활성
        return {"billing_enabled": False}
    return {
        "billing_enabled": True,
        "quota": billing.quota_status(user["id"]),
        "recent": billing.recent_events(user["id"], limit=20),
    }


@app.post("/api/pipeline/run")
async def api_run(request: PipelineRequest, user: dict = Depends(current_user)) -> dict[str, Any]:
    """전체 파이프라인 실행 (인증 + 월간 한도 적용)."""
    if BILLING_ENABLED and user["id"] != 0 and not billing.can_generate(user["id"]):
        q = billing.quota_status(user["id"])
        raise HTTPException(
            status_code=402,  # Payment Required
            detail=(
                f"이번 달 무료 한도({q['monthly_paper_limit']}편)를 모두 사용했습니다. "
                f"Pro 플랜으로 업그레이드하면 무제한 생성이 가능합니다. (사용 {q['used_this_month']}편)"
            ),
        )
    try:
        result = await pipeline.run(request)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}") from exc

    if BILLING_ENABLED and user["id"] != 0:
        billing.record_paper(
            user["id"],
            request.topic,
            {"passed": result.passed, "total": (result.evaluation.total if result.evaluation else None)},
        )
    out = result.to_public_dict()
    if BILLING_ENABLED and user["id"] != 0:
        out["quota"] = billing.quota_status(user["id"])
    return out


def _require(payload: dict[str, Any], key: str) -> Any:
    if key not in payload:
        raise HTTPException(status_code=422, detail=f"'{key}' is required")
    return payload[key]


@app.post("/api/stage1")
async def api_stage1(payload: dict[str, Any], user: dict = Depends(current_user)) -> dict[str, Any]:
    result = await pipeline.stage1_parallel_search(_require(payload, "topic"), payload.get("keywords") or [])
    return result.model_dump(mode="json")


@app.post("/api/stage2")
async def api_stage2(payload: dict[str, Any], user: dict = Depends(current_user)) -> dict[str, Any]:
    result = await pipeline.stage2_dedup_normalize(Stage1Result.model_validate(_require(payload, "stage1")))
    return result.model_dump(mode="json")


@app.post("/api/stage3")
async def api_stage3(payload: dict[str, Any], user: dict = Depends(current_user)) -> dict[str, Any]:
    result = await pipeline.stage3_researcher(
        _require(payload, "topic"),
        Stage1Result.model_validate(_require(payload, "stage1")),
        Stage2Result.model_validate(_require(payload, "stage2")),
    )
    return result.model_dump(mode="json")


@app.post("/api/stage4")
async def api_stage4(payload: dict[str, Any], user: dict = Depends(current_user)) -> dict[str, Any]:
    result = await pipeline.stage4_generator(
        _require(payload, "topic"),
        EvidenceStructure.model_validate(_require(payload, "evidence")),
        Stage2Result.model_validate(_require(payload, "stage2")),
        iteration=int(payload.get("iteration", 1)),
        feedback=payload.get("feedback", ""),
    )
    return result.model_dump(mode="json")


@app.post("/api/stage5")
async def api_stage5(payload: dict[str, Any], user: dict = Depends(current_user)) -> dict[str, Any]:
    from models import PaperDraft

    result = await pipeline.stage5_proofreader(PaperDraft(body_markdown=_require(payload, "markdown")))
    return result.model_dump(mode="json")


@app.post("/api/stage6")
async def api_stage6(payload: dict[str, Any], user: dict = Depends(current_user)) -> dict[str, Any]:
    result = await pipeline.stage6_evaluator(
        _require(payload, "markdown"), float(payload.get("gate_threshold", 70.0))
    )
    return result.model_dump(mode="json")


# ----- Stripe 웹훅 ---------------------------------------------------------- #
@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request) -> dict[str, Any]:
    """Stripe 결제 이벤트 수신 → 구독 상태 갱신."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = billing.verify_and_parse_webhook(payload, sig)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return billing.handle_stripe_event(event)


# ----- Stripe Checkout (결제 페이지 세션 생성) ------------------------------ #
@app.post("/api/checkout")
async def api_checkout(payload: dict[str, Any] | None = None, user: dict = Depends(current_user)) -> dict[str, Any]:
    """Pro 구독 결제를 위한 Stripe Checkout 세션 생성 → 결제 URL 반환."""
    if user.get("id", 0) == 0 or not user.get("api_key"):
        raise HTTPException(status_code=400, detail="유효한 API 키 사용자만 결제할 수 있습니다.")
    if not billing.stripe_configured():
        raise HTTPException(
            status_code=501,
            detail="Stripe 미설정: STRIPE_SECRET_KEY 와 STRIPE_PRICE_PRO 환경변수를 설정하세요.",
        )
    payload = payload or {}
    success = payload.get("success_url", "https://example.com/success")
    cancel = payload.get("cancel_url", "https://example.com/cancel")
    plan = payload.get("plan", "pro")
    try:
        return billing.create_checkout_session(user["api_key"], success, cancel, plan)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Checkout 생성 실패: {exc}") from exc


# ----- 비동기 작업 큐 (긴 논문 생성을 job 으로 처리) ------------------------- #
async def _run_job(job_id: str, request: PipelineRequest, user_id: int) -> None:
    jobs.set_running(job_id)
    try:
        result = await pipeline.run(request)
        if BILLING_ENABLED and user_id != 0:
            billing.record_paper(
                user_id, request.topic,
                {"passed": result.passed, "total": (result.evaluation.total if result.evaluation else None)},
            )
        jobs.set_result(job_id, result.to_public_dict())
    except Exception as exc:  # noqa: BLE001
        jobs.set_error(job_id, f"{type(exc).__name__}: {exc}")


@app.post("/api/pipeline/jobs")
async def api_create_job(request: PipelineRequest, user: dict = Depends(current_user)) -> dict[str, Any]:
    """논문 생성을 비동기 job 으로 시작. 즉시 job_id 반환(타임아웃 회피)."""
    if BILLING_ENABLED and user["id"] != 0 and not billing.can_generate(user["id"]):
        q = billing.quota_status(user["id"])
        raise HTTPException(
            status_code=402,
            detail=f"이번 달 무료 한도({q['monthly_paper_limit']}편)를 모두 사용했습니다. Pro로 업그레이드하세요.",
        )
    job_id = jobs.create_job(user["id"], request.topic)
    asyncio.create_task(_run_job(job_id, request, user["id"]))
    return {"job_id": job_id, "status": "queued", "poll": f"/api/pipeline/jobs/{job_id}"}


@app.get("/api/pipeline/jobs/{job_id}")
async def api_get_job(job_id: str, user: dict = Depends(current_user)) -> dict[str, Any]:
    """job 상태/결과 조회."""
    job = jobs.get_job(job_id, user_id=(None if user["id"] == 0 else user["id"]))
    if not job:
        raise HTTPException(status_code=404, detail="job 을 찾을 수 없습니다.")
    return job


@app.get("/api/pipeline/jobs")
async def api_list_jobs(user: dict = Depends(current_user)) -> dict[str, Any]:
    """내 job 목록."""
    if user["id"] == 0:
        return {"jobs": []}
    return {"jobs": jobs.list_jobs(user["id"])}


# ----- 랜딩/대시보드 (간단 HTML) -------------------------------------------- #
_LANDING_HTML = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>논문생산 파이프라인 v2</title>
<style>
 body{font-family:system-ui,-apple-system,'Malgun Gothic',sans-serif;max-width:860px;margin:40px auto;padding:0 16px;color:#1a1a2e;line-height:1.6}
 h1{font-size:1.9rem} .sub{color:#555}
 .plans{display:flex;gap:16px;flex-wrap:wrap;margin:24px 0}
 .card{flex:1;min-width:220px;border:1px solid #e0e0e8;border-radius:12px;padding:20px}
 .card.pro{border-color:#4a6cf7;box-shadow:0 4px 16px rgba(74,108,247,.12)}
 .price{font-size:1.6rem;font-weight:700;margin:8px 0}
 .badge{display:inline-block;background:#4a6cf7;color:#fff;border-radius:6px;padding:2px 8px;font-size:.75rem}
 code{background:#f4f4f8;padding:2px 6px;border-radius:4px}
 ul{padding-left:18px} li{margin:4px 0}
</style></head><body>
<h1>논문생산 무인 파이프라인 v2</h1>
<p class="sub">주제만 입력하면 한국특수체육학회지 양식의 SEM 논문 초안과 DOCX를 자동 생성합니다.</p>
<div class="plans">
 <div class="card"><span class="badge" style="background:#888">Free</span>
  <div class="price">$0<span style="font-size:.9rem;color:#888">/월</span></div>
  <ul><li>월 3편 생성</li><li>DOCX 내보내기</li><li>문헌 자동 수집</li></ul></div>
 <div class="card pro"><span class="badge">Pro</span>
  <div class="price">$29<span style="font-size:.9rem;color:#888">/월</span></div>
  <ul><li>무제한 생성</li><li>우선 처리</li><li>생성 이력 보관</li><li>이메일 지원</li></ul></div>
 <div class="card"><span class="badge" style="background:#333">Enterprise</span>
  <div class="price">문의</div>
  <ul><li>팀 좌석 · 온프레미스</li><li>SSO · 감사로그</li><li>전용 지원 · SLA</li></ul></div>
</div>
<h3>시작하기</h3>
<ol>
 <li>API 키 발급: <code>POST /api/signup</code></li>
 <li>플랜 확인: <code>GET /api/plans</code> · 사용량: <code>GET /api/usage</code></li>
 <li>논문 생성(비동기): <code>POST /api/pipeline/jobs</code> → <code>GET /api/pipeline/jobs/{id}</code></li>
 <li>Pro 결제: <code>POST /api/checkout</code></li>
</ol>
<p class="sub">⚠️ 생성 결과의 통계·인용은 초안용 예시 수치입니다. 실제 게재 전 실측 데이터로 검증하세요.</p>
</body></html>"""


@app.get("/", response_class=HTMLResponse)
async def landing() -> str:
    return _LANDING_HTML


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "mcp_server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
