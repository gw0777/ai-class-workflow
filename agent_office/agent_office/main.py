"""진입점: 디스코드 봇 무리 + 대시보드 + 하트비트/리마인더를 한 프로세스에서 돌린다.

    python -m agent_office            # 전체 가동
    python -m agent_office --check    # 설정·채널·토큰 점검만
    python -m agent_office --cli      # 디스코드 없이 터미널에서 역할 봇과 대화(승인은 y/n)
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

import uvicorn

from .config import Settings, load_office_config
from .dashboard import create_app
from .heartbeat import heartbeat_loop, reminder_loop
from .office import Office

log = logging.getLogger("agent_office")


def check(settings: Settings) -> int:
    cfg = load_office_config(settings.agents_yaml, settings)
    print(f"역할 {len(cfg.roles)}개 / 소유자 ID {settings.owner_discord_id or cfg.owner.discord_id or '(미설정)'}")
    ok = True
    for r in cfg.roles:
        tok = settings.role_token(r.key)
        print(f"  {r.emoji} {r.name:<4} #{r.channel:<5} {cfg.model_for(r):<18} effort={cfg.effort_for(r):<6} "
              f"토큰={'있음' if tok else '없음'} 도구={','.join(r.tools)}")
        ok &= bool(tok)
    if not settings.anthropic_api_key and not settings.dry_run:
        print("  ! ANTHROPIC_API_KEY 미설정 (DRY_RUN=true 면 생략 가능)")
    if not settings.owner_discord_id and not cfg.owner.discord_id:
        print("  ! OWNER_DISCORD_ID 미설정 → 승인 권한자가 없어 모든 요청이 무시됩니다")
        ok = False
    print("채널 목록(디스코드 서버에 같은 이름으로 만들 것):",
          ", ".join(f"#{r.channel}" for r in cfg.roles) + f", #{cfg.owner.heartbeat_channel}")
    return 0 if ok else 1


async def run_all(settings: Settings) -> None:
    from .bot import DiscordFleet, DiscordTransport

    transport = DiscordTransport()
    office = Office.build(settings, transport=transport)
    fleet = DiscordFleet(office, transport)
    fleet.register_roles()

    server = uvicorn.Server(uvicorn.Config(create_app(office), host=settings.dashboard_host,
                                           port=settings.dashboard_port, log_level="warning"))
    tasks = [asyncio.create_task(fleet.run()), asyncio.create_task(server.serve()),
             asyncio.create_task(reminder_loop(office))]
    if settings.heartbeat_enabled:
        async def delayed_heartbeat() -> None:
            await asyncio.sleep(15)       # 디스코드 로그인·길드 캐시가 채워질 시간
            await heartbeat_loop(office)
        tasks.append(asyncio.create_task(delayed_heartbeat()))
    log.info("대시보드 http://%s:%s", settings.dashboard_host, settings.dashboard_port)
    try:
        await asyncio.gather(*tasks)
    finally:
        await fleet.close()


async def run_cli(settings: Settings) -> None:
    """디스코드 없이 터미널 대화(배선·프롬프트 점검용)."""
    from .transport import FakeTransport

    transport = FakeTransport()
    office = Office.build(settings, transport=transport)
    printed = 0

    async def on_request(message_id: str) -> None:
        nonlocal printed
        for m in transport.sent[printed:]:
            print(f"\n[#{m.channel}] {m.text}")
        printed = len(transport.sent)
        ans = await asyncio.get_running_loop().run_in_executor(None, input, "승인? (y/n) ")
        rec = office.memory.find_approval_by_message(message_id)
        if rec:
            office.gate.resolve(int(rec["id"]), ans.strip().lower().startswith("y"))

    transport.on_approval_request = on_request
    print("채널 이름을 붙여 입력하세요. 예) 연구실: 특수체육 협동학습 논문 주제 3개 제안해줘   (종료: quit)")
    while True:
        line = await asyncio.get_running_loop().run_in_executor(None, input, "> ")
        if line.strip() in ("quit", "exit"):
            break
        channel, _, text = line.partition(":")
        if not text:
            print("형식: <채널>: <요청>")
            continue
        await office.handle_message(channel=channel.strip(), author_id=office.owner_id, text=text.strip())
        await office.wait_idle()
        for m in transport.sent[printed:]:
            print(f"\n[#{m.channel}] {m.text}")
        printed = len(transport.sent)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent_office")
    parser.add_argument("--check", action="store_true", help="설정 점검만")
    parser.add_argument("--cli", action="store_true", help="터미널 모드")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = Settings()
    if args.check:
        return check(settings)
    if args.cli:
        asyncio.run(run_cli(settings))
        return 0
    try:
        asyncio.run(run_all(settings))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
