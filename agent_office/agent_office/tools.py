"""역할 봇이 쓰는 도구들.

도구 이름이 config/agents.yaml 의 approval_required_tools 에 있으면 실행 전에 승인 게이트를 거친다.
외부 비용이 드는 것(논문 파이프라인), 바깥으로 나가는 것(메일), 디스크에 쓰는 것(파일)이 대상이다.
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .config import REPO_DIR, RoleConfig, enforce_terms

if TYPE_CHECKING:  # pragma: no cover
    from .office import Office


@dataclass
class ToolContext:
    office: Office
    role: RoleConfig
    task_id: int
    channel: str


Handler = Callable[[ToolContext, dict[str, Any]], Awaitable[str]]


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Handler

    def to_api(self) -> dict[str, Any]:
        schema = dict(self.input_schema)
        schema.setdefault("type", "object")
        schema.setdefault("additionalProperties", False)
        schema.setdefault("required", [])
        return {"name": self.name, "description": self.description, "input_schema": schema, "strict": True}


def _schema(props: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": props, "required": required, "additionalProperties": False}


_SAFE_NAME = re.compile(r"[^0-9A-Za-z가-힣._ -]+")


def safe_filename(name: str) -> str:
    name = Path(name).name                      # 경로 구성요소 제거(상위 디렉터리 탈출 방지)
    name = _SAFE_NAME.sub("_", name).strip(" .") or "untitled.md"
    return name[:120]


# --------------------------------------------------------------------------- #
# 핸들러
# --------------------------------------------------------------------------- #
async def _delegate(ctx: ToolContext, inp: dict[str, Any]) -> str:
    to_role = inp["role"]
    try:
        ctx.office.config.role(to_role)
    except KeyError:
        return f"오류: 역할 '{to_role}' 없음. 가능한 역할: " + ", ".join(r.key for r in ctx.office.config.roles)
    task_id = await ctx.office.handoff(
        from_role=ctx.role.key, to_role=to_role, task=inp["task"],
        done_criteria=inp.get("done_criteria", ""), done_line=inp.get("done_line", ""),
        parent_task_id=ctx.task_id,
    )
    return f"넘김 완료: #{task_id} → {to_role}. 담당 채널에 완료 기준과 함께 기록했습니다."


async def _list_tasks(ctx: ToolContext, inp: dict[str, Any]) -> str:
    status = inp.get("status") or None
    scope_all = bool(inp.get("all_roles", False))
    tasks = ctx.office.memory.list_tasks(None if scope_all else ctx.role.key, status, limit=20)
    if not tasks:
        return "작업 없음"
    lines = [f"#{t['id']} [{t['status']}] ({t['role']}) {t['title'][:80]}"
             + (f" — 완료 기준: {t['done_criteria'][:60]}" if t['done_criteria'] else "") for t in tasks]
    return "\n".join(lines)


async def _daily_briefing(ctx: ToolContext, inp: dict[str, Any]) -> str:
    from .heartbeat import compose_status
    return compose_status(ctx.office)


async def _spawn_subagent(ctx: ToolContext, inp: dict[str, Any]) -> str:
    cfg = ctx.office.config
    model = inp.get("model") or cfg.defaults.subagent_model
    system = (
        f"당신은 {ctx.role.name}({ctx.role.title})의 팀원 봇입니다. 지시받은 하위 작업만 간결하게 처리하고 "
        "결과만 돌려주세요. 용어: '적응체육' 대신 반드시 '특수체육'을 씁니다."
    )
    user = inp["instruction"] + ("\n\n[맥락]\n" + inp["context"] if inp.get("context") else "")
    resp = await ctx.office.llm.complete(model=model, system=system, messages=[{"role": "user", "content": user}],
                                         tools=None, effort=cfg.defaults.subagent_effort, max_tokens=8000)
    ctx.office.memory.add_usage(ctx.role.key, resp.model, resp.usage.input_tokens, resp.usage.output_tokens,
                                resp.usage.cache_read_tokens)
    ctx.office.memory.log_event(ctx.role.key, "tool", f"팀원 봇({model}) 호출: {inp['instruction'][:80]}")
    return enforce_terms(resp.text) or "(팀원 봇 응답 없음)"


async def _run_paper_pipeline(ctx: ToolContext, inp: dict[str, Any]) -> str:
    import httpx

    s = ctx.office.settings
    url = s.paper_pipeline_url.rstrip("/") + "/api/pipeline/run"
    headers = {"Content-Type": "application/json"}
    if s.paper_pipeline_api_key:
        headers["X-API-Key"] = s.paper_pipeline_api_key
    body = {"topic": inp["topic"], "max_iterations": int(inp.get("max_iterations", 3)),
            "gate_threshold": int(inp.get("gate_threshold", 70))}
    try:
        async with httpx.AsyncClient(timeout=3600) as client:
            r = await client.post(url, json=body, headers=headers)
    except httpx.HTTPError as e:
        return f"파이프라인 서버 연결 실패({url}): {e}. paper_pipeline_v2 서버가 떠 있는지 확인하세요."
    if r.status_code == 402:
        return "파이프라인 월간 한도 초과(HTTP 402)."
    if r.status_code >= 400:
        return f"파이프라인 오류 HTTP {r.status_code}: {r.text[:300]}"
    data = r.json()
    return json.dumps({k: data.get(k) for k in ("passed", "final_score", "iterations", "saved_path", "job_id")
                       if k in data} or data, ensure_ascii=False)[:1500]


async def _similarity_check(ctx: ToolContext, inp: dict[str, Any]) -> str:
    path = Path(inp["path"])
    if not path.is_absolute():
        path = (ctx.office.settings.office_output_dir / ctx.role.key / path).resolve()
    if not path.exists():
        return f"파일 없음: {path}"
    out_dir = ctx.office.settings.office_output_dir / ctx.role.key / "similarity_reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "similarity_checker", "check", str(path), "--out-dir", str(out_dir)]
    if inp.get("refs", True):
        cmd.append("--refs")
    if inp.get("online", False):
        cmd.append("--online")
    proc = await asyncio.create_subprocess_exec(*cmd, cwd=str(REPO_DIR), stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.STDOUT)
    out, _ = await asyncio.wait_for(proc.communicate(), timeout=1800)
    text = out.decode("utf-8", "replace")
    return f"(종료코드 {proc.returncode}) 리포트 폴더: {out_dir}\n" + text[-1500:]


async def _write_file(ctx: ToolContext, inp: dict[str, Any]) -> str:
    base = ctx.office.settings.office_output_dir / ctx.role.key
    base.mkdir(parents=True, exist_ok=True)
    target = base / safe_filename(inp["filename"])
    target.write_text(enforce_terms(inp["content"]), encoding="utf-8")
    ctx.office.memory.log_event(ctx.role.key, "tool", f"파일 저장: {target}")
    return f"저장됨: {target}"


async def _send_email_draft(ctx: ToolContext, inp: dict[str, Any]) -> str:
    draft_id = ctx.office.memory.add_draft(ctx.role.key, "email", enforce_terms(inp["body"]),
                                           inp.get("recipient", ""), enforce_terms(inp.get("subject", "")))
    return (f"메일 초안 #{draft_id} 저장(수신: {inp.get('recipient', '-')}, 제목: {inp.get('subject', '-')}). "
            "실제 발송은 이 시스템이 하지 않습니다 — 교수님이 메일 앱에서 보내세요.")


async def _remind(ctx: ToolContext, inp: dict[str, Any]) -> str:
    rid = ctx.office.memory.add_reminder(ctx.role.key, inp["due_at"], enforce_terms(inp["text"]))
    return f"리마인더 #{rid} 등록: {inp['due_at']} — {inp['text'][:80]}"


# --------------------------------------------------------------------------- #
# 레지스트리
# --------------------------------------------------------------------------- #
REGISTRY: dict[str, ToolSpec] = {
    "delegate": ToolSpec(
        "delegate",
        "다른 담당 봇에게 일을 넘긴다. 넘기기 전에 내가 한 일 한 줄(done_line)과 '이렇게 되면 끝'(done_criteria)을 반드시 적는다.",
        _schema({
            "role": {"type": "string", "description": "받을 역할 key: research|teaching|society|center|writer|secretary|manager"},
            "task": {"type": "string", "description": "넘길 일(구체적으로)"},
            "done_criteria": {"type": "string", "description": "완료 기준 한 줄"},
            "done_line": {"type": "string", "description": "넘기기 전에 내가 한 일 한 줄"},
        }, ["role", "task", "done_criteria", "done_line"]),
        _delegate),
    "list_tasks": ToolSpec(
        "list_tasks", "작업 목록 조회(기본: 내 역할, all_roles=true면 전체).",
        _schema({"status": {"type": "string", "description": "queued|running|awaiting_approval|done|failed|blocked 또는 빈 문자열"},
                 "all_roles": {"type": "boolean"}}, ["status", "all_roles"]),
        _list_tasks),
    "daily_briefing": ToolSpec("daily_briefing", "전체 봇 상태·오늘 토큰 사용량·대기 승인·최근 넘김 요약.",
                               _schema({}, []), _daily_briefing),
    "spawn_subagent": ToolSpec(
        "spawn_subagent",
        "값싼 모델의 팀원 봇에게 단순 하위 작업(요약·목록화·초안 변환 등)을 맡긴다. 복잡한 판단은 맡기지 않는다.",
        _schema({"instruction": {"type": "string"}, "context": {"type": "string"},
                 "model": {"type": "string", "description": "비워두면 기본 서브에이전트 모델"}},
                ["instruction", "context", "model"]),
        _spawn_subagent),
    "run_paper_pipeline": ToolSpec(
        "run_paper_pipeline",
        "paper_pipeline_v2 서버로 SEM 논문 자동생산(7단계, 품질 GATE)을 실행한다. 비용이 크므로 승인 필요.",
        _schema({"topic": {"type": "string"}, "max_iterations": {"type": "integer"},
                 "gate_threshold": {"type": "integer"}}, ["topic", "max_iterations", "gate_threshold"]),
        _run_paper_pipeline),
    "similarity_check": ToolSpec(
        "similarity_check",
        "similarity_checker로 문서의 유사도·표절률·참고문헌 실존 여부를 검사하고 리포트를 만든다.",
        _schema({"path": {"type": "string", "description": "검사할 파일 경로(상대경로면 내 출력 폴더 기준)"},
                 "refs": {"type": "boolean"}, "online": {"type": "boolean"}}, ["path", "refs", "online"]),
        _similarity_check),
    "write_file": ToolSpec(
        "write_file", "결과물을 내 출력 폴더에 파일로 저장한다(마크다운 권장). 저장 전 승인 필요.",
        _schema({"filename": {"type": "string"}, "content": {"type": "string"}}, ["filename", "content"]),
        _write_file),
    "send_email_draft": ToolSpec(
        "send_email_draft", "메일 초안을 저장한다(발송하지 않음). 승인 필요.",
        _schema({"recipient": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}},
                ["recipient", "subject", "body"]),
        _send_email_draft),
    "remind": ToolSpec(
        "remind", "리마인더 등록. due_at은 ISO 8601(예: 2026-11-20T09:00:00+09:00).",
        _schema({"due_at": {"type": "string"}, "text": {"type": "string"}}, ["due_at", "text"]),
        _remind),
}


def tools_for(role: RoleConfig) -> list[ToolSpec]:
    return [REGISTRY[name] for name in role.tools if name in REGISTRY]
