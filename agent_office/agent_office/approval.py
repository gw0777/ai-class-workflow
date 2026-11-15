"""승인 가드레일.

"모든 작업은 최종적으로 소유자의 승인을 받는다" — 비용이 들거나 바깥으로 나가는 도구는
실행 전에 채널에 승인 메시지를 올리고 ✅/❌ 반응을 기다린다. 결과는 DB에도 남긴다.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from .memory import Memory
from .transport import APPROVE_EMOJI, DENY_EMOJI, Transport


class ApprovalGate:
    def __init__(self, memory: Memory, transport: Transport, owner_id: int, timeout_sec: int = 86400) -> None:
        self.memory = memory
        self.transport = transport
        self.owner_id = owner_id
        self.timeout_sec = timeout_sec
        self._waiters: dict[int, asyncio.Future[bool]] = {}

    def format_request(self, approval_id: int, role_name: str, tool: str, summary: str,
                       payload: dict[str, Any]) -> str:
        preview = json.dumps(payload, ensure_ascii=False, indent=1)
        if len(preview) > 700:
            preview = preview[:700] + " …"
        return (
            f"🔒 **승인 요청 #{approval_id}** — {role_name} → `{tool}`\n"
            f"{summary}\n"
            f"```json\n{preview}\n```\n"
            f"{APPROVE_EMOJI} 승인  /  {DENY_EMOJI} 거부   (응답 없으면 {self.timeout_sec // 3600}시간 후 만료)"
        )

    async def request(self, *, role_key: str, role_name: str, channel: str, tool: str, summary: str,
                      payload: dict[str, Any], task_id: int | None = None) -> bool:
        approval_id = self.memory.create_approval(role_key, task_id, tool, summary, payload, channel)
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[bool] = loop.create_future()
        self._waiters[approval_id] = fut
        text = self.format_request(approval_id, role_name, tool, summary, payload)
        message_id = await self.transport.send(channel, text)
        self.memory.set_approval_message(approval_id, message_id)
        self.memory.log_event(role_key, "approval", f"요청 #{approval_id} {tool}: {summary}")
        if task_id:
            self.memory.update_task(task_id, status="awaiting_approval")
        await self.transport.add_reactions(channel, message_id, [APPROVE_EMOJI, DENY_EMOJI])
        try:
            approved = await asyncio.wait_for(fut, timeout=self.timeout_sec)
        except TimeoutError:
            self.memory.resolve_approval(approval_id, "expired")
            self.memory.log_event(role_key, "approval", f"#{approval_id} 만료")
            await self.transport.send(channel, f"⏰ 승인 요청 #{approval_id} 이(가) 만료되어 실행하지 않았습니다.")
            return False
        finally:
            self._waiters.pop(approval_id, None)
        if task_id:
            self.memory.update_task(task_id, status="running")
        return approved

    def resolve(self, approval_id: int, approved: bool, by_user_id: int | None = None) -> bool:
        """반응/명령으로 승인 결과를 반영. 소유자가 아니면 무시."""
        if by_user_id is not None and self.owner_id and by_user_id != self.owner_id:
            return False
        rec = self.memory.get_approval(approval_id)
        if not rec or rec["status"] != "pending":
            return False
        self.memory.resolve_approval(approval_id, "approved" if approved else "denied")
        self.memory.log_event(rec["role"], "approval", f"#{approval_id} {'승인' if approved else '거부'}")
        fut = self._waiters.get(approval_id)
        if fut is not None and not fut.done():
            fut.set_result(approved)
        return True

    def resolve_by_message(self, message_id: str, emoji: str, by_user_id: int | None) -> bool:
        if emoji not in (APPROVE_EMOJI, DENY_EMOJI):
            return False
        rec = self.memory.find_approval_by_message(message_id)
        if not rec:
            return False
        return self.resolve(int(rec["id"]), emoji == APPROVE_EMOJI, by_user_id)
