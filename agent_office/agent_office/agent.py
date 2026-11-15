"""역할 봇 한 개의 실행 루프: 시스템 프롬프트 → Claude 호출 → 도구 실행(승인 게이트) → 한 줄 기록."""
from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from .config import RoleConfig, enforce_terms
from .tools import ToolContext, tools_for

if TYPE_CHECKING:  # pragma: no cover
    from .office import Office

MAX_TOOL_ROUNDS = 12
DONE_LINE_RE = re.compile(r"^\s*(?:📝\s*)?한\s*일\s*[:：]\s*(.+)$", re.MULTILINE)

COMMON_RULES = """\
[공통 규칙]
1. 용어: '적응체육'이라는 말은 절대 쓰지 않는다. 항상 '특수체육'으로 쓴다.
2. 한국어로, 짧고 구체적으로 답한다. 모르는 것은 아는 척하지 말고 교수님께 질문한다.
3. 바깥으로 나가거나 비용이 드는 일(파일 저장, 메일 초안, 논문 파이프라인 실행)은 도구를 통해 승인 요청이 올라간다. \
승인이 거부되면 그 이유를 묻고 멈춘다.
4. 작업을 끝내거나 다른 봇에게 넘길 때는 마지막 줄에 반드시 `한 일: <한 줄>` 을 남긴다. \
이 한 줄은 채널과 기록부에 남아 나중에 '그때 왜 그렇게 판단했지'를 찾을 때 쓰인다.
5. 완료 기준('이렇게 되면 끝')이 주어지면 그 기준을 충족했는지 스스로 점검하고 결과에 적는다. 기준이 없으면 먼저 한 줄로 정하고 시작한다.
6. 통계·예산·인용 수치는 출처를 쓰고, 생성한 수치는 '가상 수치'라고 표시한다.
"""


def build_system_prompt(office: Office, role: RoleConfig) -> str:
    cfg = office.config
    colleagues = "\n".join(
        f"- {r.key} = {r.name}({r.title}) · 채널 #{r.channel}" for r in cfg.roles if r.key != role.key)
    tool_names = ", ".join(role.tools) or "없음"
    # 역할 설명(purpose/done_criteria)은 config 검증 단계에서 이미 용어가 통일돼 있다.
    # COMMON_RULES 에는 금지 용어가 "쓰지 말라"는 문장으로 들어 있으므로 여기서 치환하면 안 된다.
    return (
        f"당신은 {cfg.owner.display_name}의 AI 사무실에서 일하는 '{role.name}' 봇입니다. 직함: {role.title}. "
        f"담당 채널: #{role.channel}.\n\n"
        f"[역할]\n{enforce_terms(role.purpose)}\n\n"
        f"[이렇게 되면 끝 — 기본 완료 기준]\n{enforce_terms(role.done_criteria)}\n\n"
        f"[동료 봇]\n{colleagues}\n\n"
        f"[사용 가능한 도구] {tool_names}\n\n" + COMMON_RULES
    )


def extract_done_line(text: str) -> str:
    m = DONE_LINE_RE.findall(text)
    if m:
        return m[-1].strip()[:300]
    first = text.strip().splitlines()[0] if text.strip() else ""
    return first[:120]


class RoleAgent:
    def __init__(self, office: Office, role: RoleConfig) -> None:
        self.office = office
        self.role = role
        self.tools = tools_for(role)
        self._tool_map = {t.name: t for t in self.tools}
        self.busy = False

    # ------------------------------------------------------------------ #
    def _budget_exceeded(self) -> tuple[bool, int, int]:
        used = self.office.memory.usage_today(self.role.key)["total"]
        budget = self.office.config.budget_for(self.role)
        return used >= budget, used, budget

    async def _check_budget(self, task_id: int) -> bool:
        exceeded, used, budget = self._budget_exceeded()
        if not exceeded:
            return True
        ok = await self.office.gate.request(
            role_key=self.role.key, role_name=self.role.name, channel=self.role.channel, tool="budget_override",
            summary=f"오늘 토큰 예산 초과(사용 {used:,} / 예산 {budget:,}). 계속 진행할까요?",
            payload={"used": used, "budget": budget}, task_id=task_id)
        if not ok:
            self.office.memory.update_task(task_id, status="blocked", done_line="예산 초과로 중단")
        return ok

    async def _run_tool(self, name: str, inp: dict[str, Any], task_id: int) -> str:
        spec = self._tool_map.get(name)
        if spec is None:
            return f"오류: 이 역할은 '{name}' 도구를 쓸 수 없습니다."
        mem = self.office.memory
        if self.office.config.requires_approval(name):
            summary = _summarize_tool_call(name, inp)
            approved = await self.office.gate.request(
                role_key=self.role.key, role_name=self.role.name, channel=self.role.channel, tool=name,
                summary=summary, payload=inp, task_id=task_id)
            if not approved:
                mem.log_event(self.role.key, "tool", f"{name} 거부/만료")
                return f"소유자가 '{name}' 실행을 승인하지 않았습니다. 이유를 묻고 멈추세요."
        ctx = ToolContext(office=self.office, role=self.role, task_id=task_id, channel=self.role.channel)
        try:
            result = await spec.handler(ctx, inp)
        except Exception as e:  # noqa: BLE001 - 도구 실패는 모델에게 돌려주고 루프는 계속
            mem.log_event(self.role.key, "error", f"{name}: {e!r}")
            return f"도구 오류({name}): {e!r}"
        mem.log_event(self.role.key, "tool", f"{name}: {str(result)[:160]}")
        return str(result)

    # ------------------------------------------------------------------ #
    async def run(self, request: str, *, origin: str = "owner", done_criteria: str = "",
                  task_id: int | None = None) -> str:
        """요청 하나를 끝까지 처리하고 최종 답변 텍스트를 돌려준다(채널 전송은 Office가 한다)."""
        office, mem, cfg = self.office, self.office.memory, self.office.config
        if task_id is None:
            task_id = mem.create_task(self.role.key, self.role.channel, request, done_criteria, origin)
        mem.update_task(task_id, status="running")
        mem.log_event(self.role.key, "message", f"[{origin}] {request[:200]}")
        self.busy = True
        try:
            if not await self._check_budget(task_id):
                return "오늘 토큰 예산을 초과했고 추가 진행이 승인되지 않아 멈춥니다."

            system = build_system_prompt(office, self.role)
            user_text = request
            if done_criteria:
                user_text += f"\n\n[완료 기준] {done_criteria}"
            if origin.startswith("handoff:"):
                user_text = f"[{origin.split(':', 1)[1]} 봇이 넘긴 일]\n" + user_text
            messages: list[dict[str, Any]] = [{"role": "user", "content": user_text}]
            api_tools = [t.to_api() for t in self.tools] or None
            model, effort, max_tokens = cfg.model_for(self.role), cfg.effort_for(self.role), cfg.max_tokens_for(self.role)

            final_text = ""
            for _ in range(MAX_TOOL_ROUNDS):
                resp = await office.llm.complete(model=model, system=system, messages=messages, tools=api_tools,
                                                 effort=effort, max_tokens=max_tokens)
                mem.add_usage(self.role.key, resp.model, resp.usage.input_tokens, resp.usage.output_tokens,
                              resp.usage.cache_read_tokens)
                if resp.stop_reason == "refusal":
                    final_text = (f"요청이 안전 정책으로 거절되었습니다(category={resp.refusal_category}). "
                                  "표현을 바꿔 다시 요청해 주세요.")
                    mem.update_task(task_id, status="failed", done_line=final_text[:120])
                    break
                if resp.stop_reason == "max_tokens":
                    final_text = (resp.text or "") + "\n\n(출력 길이 한도에 걸려 잘렸습니다. 이어서 요청해 주세요.)"
                    break
                if resp.stop_reason == "pause_turn":
                    messages.append({"role": "assistant", "content": resp.content})
                    continue
                if not resp.tool_calls:
                    final_text = resp.text
                    break
                messages.append({"role": "assistant", "content": resp.content})
                results = []
                for call in resp.tool_calls:
                    out = await self._run_tool(call.name, call.input, task_id)
                    results.append({"type": "tool_use_id", "id": call.id, "out": out})
                messages.append({"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": r["id"], "content": r["out"]} for r in results]})
                if not await self._check_budget(task_id):
                    final_text = "도구 실행 중 토큰 예산을 초과해 멈췄습니다."
                    break
            else:
                final_text = resp.text or "도구 호출 횟수 한도에 도달해 멈췄습니다. 범위를 좁혀 다시 요청해 주세요."

            final_text = enforce_terms(final_text or "(응답 없음)")
            done_line = extract_done_line(final_text)
            task = mem.get_task(task_id) or {}
            if task.get("status") not in ("failed", "blocked"):
                mem.update_task(task_id, status="done", done_line=done_line)
            mem.log_event(self.role.key, "message", f"완료 #{task_id}: {done_line}")
            return final_text
        finally:
            self.busy = False


def _summarize_tool_call(name: str, inp: dict[str, Any]) -> str:
    if name == "run_paper_pipeline":
        return f"논문 파이프라인 실행 — 주제: {inp.get('topic', '')[:120]} (비용 발생)"
    if name == "write_file":
        return f"파일 저장 — {inp.get('filename', '')} ({len(inp.get('content', '')):,}자)"
    if name == "send_email_draft":
        return f"메일 초안 — 수신 {inp.get('recipient', '-')}, 제목 '{inp.get('subject', '-')[:60]}'"
    if name == "spawn_subagent":
        return f"팀원 봇 호출 — {inp.get('instruction', '')[:100]}"
    return f"{name} 실행: " + json.dumps(inp, ensure_ascii=False)[:150]
