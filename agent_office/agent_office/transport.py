"""채널 전송 추상화: 디스코드 없이도(테스트·CLI) Office를 돌릴 수 있게 한다."""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Protocol

APPROVE_EMOJI = "✅"
DENY_EMOJI = "❌"


class Transport(Protocol):
    async def send(self, channel: str, text: str) -> str: ...
    async def add_reactions(self, channel: str, message_id: str, emojis: list[str]) -> None: ...


@dataclass
class SentMessage:
    channel: str
    text: str
    message_id: str
    reactions: list[str] = field(default_factory=list)


class FakeTransport:
    """보낸 메시지를 메모리에 쌓는다. 승인 자동응답을 설정할 수 있다."""

    def __init__(self, auto_approve: bool | None = None) -> None:
        self.sent: list[SentMessage] = []
        self._ids = itertools.count(1)
        self.auto_approve = auto_approve
        self.on_approval_request = None  # async callable(message) → None

    async def send(self, channel: str, text: str) -> str:
        mid = f"m{next(self._ids)}"
        self.sent.append(SentMessage(channel, text, mid))
        return mid

    async def add_reactions(self, channel: str, message_id: str, emojis: list[str]) -> None:
        for m in self.sent:
            if m.message_id == message_id:
                m.reactions.extend(emojis)
        if self.on_approval_request is not None:
            await self.on_approval_request(message_id)

    def texts(self, channel: str | None = None) -> list[str]:
        return [m.text for m in self.sent if channel is None or m.channel == channel]


def chunk_text(text: str, limit: int = 1900) -> list[str]:
    """디스코드 메시지 길이 제한(2000자)에 맞춰 자른다."""
    if len(text) <= limit:
        return [text]
    chunks, buf = [], ""
    for line in text.splitlines(keepends=True):
        if len(buf) + len(line) > limit:
            chunks.append(buf)
            buf = ""
        while len(line) > limit:
            chunks.append(line[:limit])
            line = line[limit:]
        buf += line
    if buf:
        chunks.append(buf)
    return chunks
