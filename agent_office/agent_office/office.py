"""Office: 채널 → 역할 봇 라우팅, 넘김(handoff), 명령 처리.

디스코드든 테스트용 FakeTransport든 같은 Office를 쓴다.
"""
from __future__ import annotations

import asyncio
import re
from typing import Any

from .agent import RoleAgent
from .approval import ApprovalGate
from .config import OfficeConfig, Settings, enforce_terms, load_office_config
from .llm import LLM
from .memory import Memory
from .transport import Transport, chunk_text

CMD_RE = re.compile(r"^!(상태|승인|거부|할일|도움말|help)\s*(\d+)?", re.IGNORECASE)


class Office:
    def __init__(self, *, config: OfficeConfig, settings: Settings, memory: Memory, transport: Transport,
                 llm: LLM) -> None:
        self.config = config
        self.settings = settings
        self.memory = memory
        self.transport = transport
        self.llm = llm
        owner_id = settings.owner_discord_id or config.owner.discord_id
        self.gate = ApprovalGate(memory, transport, owner_id, settings.approval_timeout_sec)
        self.agents: dict[str, RoleAgent] = {r.key: RoleAgent(self, r) for r in config.roles}
        self._background: set[asyncio.Task[Any]] = set()

    # ------------------------------------------------------------------ #
    @classmethod
    def build(cls, settings: Settings | None = None, transport: Transport | None = None,
              llm: LLM | None = None, memory: Memory | None = None) -> Office:
        from .llm import AnthropicLLM, EchoLLM
        from .transport import FakeTransport

        settings = settings or Settings()
        config = load_office_config(settings.agents_yaml, settings)
        memory = memory or Memory(settings.office_db)
        transport = transport or FakeTransport()
        if llm is None:
            llm = EchoLLM() if settings.dry_run else AnthropicLLM(settings.anthropic_api_key or None,
                                                                   settings.enable_fallbacks)
        settings.office_output_dir.mkdir(parents=True, exist_ok=True)
        return cls(config=config, settings=settings, memory=memory, transport=transport, llm=llm)

    @property
    def owner_id(self) -> int:
        return self.gate.owner_id

    def agent_for_channel(self, channel: str) -> RoleAgent | None:
        role = self.config.role_by_channel(channel)
        if role is None and channel == self.config.owner.heartbeat_channel:
            return self.agents.get("manager")       # 사무실 채널은 매니저가 받는다
        return self.agents.get(role.key) if role else None

    # ------------------------------------------------------------------ #
    async def say(self, channel: str, text: str) -> str:
        last = ""
        for part in chunk_text(enforce_terms(text)):
            last = await self.transport.send(channel, part)
        return last

    async def handle_message(self, *, channel: str, author_id: int, text: str, author_is_bot: bool = False) -> bool:
        """채널 메시지 1건 처리. 처리했으면 True."""
        if author_is_bot:
            return False
        text = text.strip()
        if not text:
            return False
        if self.owner_id and author_id != self.owner_id and not self.settings.allow_non_owner:
            return False
        if text.startswith("!"):
            return await self.handle_command(channel, author_id, text)
        agent = self.agent_for_channel(channel)
        if agent is None:
            return False
        if agent.busy:
            await self.say(channel, f"⏳ {agent.role.name} 봇이 다른 작업 중입니다. 끝나면 이어서 처리할게요.")
            self._spawn(self._run_and_reply(agent, text, "owner", ""))
            return True
        self._spawn(self._run_and_reply(agent, text, "owner", ""))
        return True

    async def _run_and_reply(self, agent: RoleAgent, request: str, origin: str, done_criteria: str,
                             task_id: int | None = None) -> None:
        try:
            reply = await agent.run(request, origin=origin, done_criteria=done_criteria, task_id=task_id)
        except Exception as e:  # noqa: BLE001 - 봇은 조용히 죽지 않는다: 채널에 오류를 남긴다
            self.memory.log_event(agent.role.key, "error", repr(e))
            reply = f"⚠️ {agent.role.name} 봇 오류: {e!r}"
        await self.say(agent.role.channel, f"{agent.role.emoji} **{agent.role.name}**\n{reply}")

    def _spawn(self, coro: Any) -> asyncio.Task[Any]:
        task = asyncio.create_task(coro)
        self._background.add(task)
        task.add_done_callback(self._background.discard)
        return task

    async def wait_idle(self) -> None:
        """테스트/CLI용: 백그라운드 작업이 모두 끝날 때까지 기다린다."""
        while self._background:
            await asyncio.gather(*list(self._background), return_exceptions=True)

    # ------------------------------------------------------------------ #
    async def handoff(self, *, from_role: str, to_role: str, task: str, done_criteria: str, done_line: str,
                      parent_task_id: int | None = None) -> int:
        """봇 → 봇 넘김. DM이 아니라 받는 봇의 채널에 공개로 남기고, 기록부에도 적는다."""
        src, dst = self.config.role(from_role), self.config.role(to_role)
        task_id = self.memory.create_task(dst.key, dst.channel, task, done_criteria, origin=f"handoff:{src.key}")
        self.memory.log_handoff(src.key, dst.key, task_id, task, done_line, done_criteria)
        if parent_task_id:
            self.memory.update_task(parent_task_id, done_line=done_line or f"→ {dst.name}에게 넘김 (#{task_id})")
        self.memory.log_event(src.key, "handoff", f"→ {dst.key} #{task_id}: {task[:120]}")
        await self.say(dst.channel,
                       f"📨 **넘김 #{task_id}** {src.emoji}{src.name} → {dst.emoji}{dst.name}\n"
                       f"• 할 일: {task}\n"
                       f"• 이렇게 되면 끝: {done_criteria or '(미정 — 받는 봇이 먼저 정함)'}\n"
                       f"• {src.name}이(가) 한 일: {done_line or '-'}")
        agent = self.agents[dst.key]
        self._spawn(self._run_and_reply(agent, task, f"handoff:{src.key}", done_criteria, task_id))
        return task_id

    # ------------------------------------------------------------------ #
    async def handle_command(self, channel: str, author_id: int, text: str) -> bool:
        m = CMD_RE.match(text)
        if not m:
            return False
        cmd, num = m.group(1).lower(), m.group(2)
        if cmd == "상태":
            from .heartbeat import compose_status
            await self.say(channel, compose_status(self))
        elif cmd in ("승인", "거부"):
            if not num:
                await self.say(channel, "사용법: `!승인 <번호>` / `!거부 <번호>`")
            elif self.gate.resolve(int(num), cmd == "승인", author_id):
                await self.say(channel, f"{'✅ 승인' if cmd == '승인' else '❌ 거부'} 처리: #{num}")
            else:
                await self.say(channel, f"#{num} 은(는) 대기 중인 승인이 아니거나 권한이 없습니다.")
        elif cmd == "할일":
            tasks = self.memory.list_tasks(limit=15)
            body = "\n".join(f"#{t['id']} [{t['status']}] {t['role']}: {t['title'][:70]}" for t in tasks) or "없음"
            await self.say(channel, "📋 최근 작업\n" + body)
        else:
            await self.say(channel, "명령: `!상태` 전체 상태 · `!할일` 최근 작업 · `!승인 N` / `!거부 N` 승인 처리")
        return True
