"""discord.py 연동.

- 역할마다 봇 토큰이 다르면(DISCORD_TOKEN_<KEY>) 봇 계정 7개가 각자 채널에서 말한다(스레드의 구성).
- 토큰 하나만 있으면(DISCORD_TOKEN) 봇 계정 1개가 7개 채널을 돌보며 역할 이름을 앞에 붙인다.
- 메시지 → Office.handle_message, ✅/❌ 반응 → 승인 게이트.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import discord

from .transport import APPROVE_EMOJI, DENY_EMOJI, chunk_text

if TYPE_CHECKING:  # pragma: no cover
    from .office import Office

log = logging.getLogger("agent_office.bot")


class DiscordTransport:
    """채널 이름 → 그 채널을 담당하는 클라이언트로 전송."""

    def __init__(self) -> None:
        self.channel_client: dict[str, discord.Client] = {}
        self.default_client: discord.Client | None = None

    def _client_for(self, channel: str) -> discord.Client | None:
        return self.channel_client.get(channel) or self.default_client

    def _find_channel(self, client: discord.Client, name: str) -> discord.TextChannel | None:
        for guild in client.guilds:
            for ch in guild.text_channels:
                if ch.name == name:
                    return ch
        return None

    async def send(self, channel: str, text: str) -> str:
        client = self._client_for(channel)
        if client is None:
            log.warning("클라이언트 없음: %s", channel)
            return ""
        ch = self._find_channel(client, channel)
        if ch is None:
            log.warning("채널 없음: #%s (디스코드 서버에 같은 이름의 텍스트 채널을 만드세요)", channel)
            return ""
        last = None
        for part in chunk_text(text):
            last = await ch.send(part)
        return str(last.id) if last else ""

    async def add_reactions(self, channel: str, message_id: str, emojis: list[str]) -> None:
        client = self._client_for(channel)
        if client is None or not message_id:
            return
        ch = self._find_channel(client, channel)
        if ch is None:
            return
        try:
            msg = await ch.fetch_message(int(message_id))
            for e in emojis:
                await msg.add_reaction(e)
        except discord.HTTPException as e:
            log.warning("반응 추가 실패: %s", e)


class DiscordFleet:
    def __init__(self, office: Office, transport: DiscordTransport) -> None:
        self.office = office
        self.transport = transport
        self.clients: dict[str, discord.Client] = {}       # token → client

    def _make_client(self, label: str) -> discord.Client:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        client = discord.Client(intents=intents)
        office = self.office

        @client.event
        async def on_ready() -> None:
            log.info("[%s] 로그인: %s", label, client.user)

        @client.event
        async def on_message(message: discord.Message) -> None:
            if message.author.bot or not isinstance(message.channel, discord.TextChannel):
                return
            # 같은 채널을 여러 클라이언트가 보고 있으면(공유 토큰 아님) 담당 클라이언트만 처리
            owner_client = self.transport._client_for(message.channel.name)
            if owner_client is not None and owner_client is not client:
                return
            await office.handle_message(channel=message.channel.name, author_id=message.author.id,
                                        text=message.content)

        @client.event
        async def on_raw_reaction_add(payload: discord.RawReactionActionEvent) -> None:
            if client.user and payload.user_id == client.user.id:
                return
            emoji = str(payload.emoji)
            if emoji not in (APPROVE_EMOJI, DENY_EMOJI):
                return
            office.gate.resolve_by_message(str(payload.message_id), emoji, payload.user_id)

        return client

    def register_roles(self) -> None:
        settings, cfg = self.office.settings, self.office.config
        for role in cfg.roles:
            token = settings.role_token(role.key)
            if not token:
                log.warning("역할 %s 토큰 없음(DISCORD_TOKEN 또는 DISCORD_TOKEN_%s)", role.key, role.key.upper())
                continue
            client = self.clients.get(token)
            if client is None:
                client = self._make_client(role.key if token != settings.discord_token else "shared")
                self.clients[token] = client
            self.transport.channel_client[role.channel] = client
        if settings.discord_token and settings.discord_token in self.clients:
            self.transport.default_client = self.clients[settings.discord_token]
        elif self.clients:
            self.transport.default_client = next(iter(self.clients.values()))
        hb = cfg.owner.heartbeat_channel
        self.transport.channel_client.setdefault(hb, self.transport.default_client)  # type: ignore[arg-type]

    async def run(self) -> None:
        if not self.clients:
            raise RuntimeError("디스코드 토큰이 하나도 없습니다. .env 의 DISCORD_TOKEN 을 확인하세요.")
        await asyncio.gather(*(client.start(token) for token, client in self.clients.items()))

    async def close(self) -> None:
        await asyncio.gather(*(c.close() for c in self.clients.values()), return_exceptions=True)
