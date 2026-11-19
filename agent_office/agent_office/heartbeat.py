"""살아있음 알림 + 상태 요약 + 리마인더 배달.

맥미니는 '조용히 죽는 것'이 제일 무섭다 → launchd KeepAlive 로 자동 재시작하고,
하루 1회(KST 지정 시각) 사무실 채널에 살아있음 + 상태 요약을 올린다.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .office import Office

KST = timezone(timedelta(hours=9))


def compose_status(office: Office) -> str:
    cfg, mem = office.config, office.memory
    usage = mem.usage_by_role_today()
    lines = [f"🏢 **사무실 상태** {datetime.now(KST).strftime('%Y-%m-%d %H:%M')} KST"]
    for r in cfg.roles:
        agent = office.agents[r.key]
        u = usage.get(r.key, {"total": 0})
        budget = cfg.budget_for(r)
        pct = (u["total"] / budget * 100) if budget else 0
        running = len(mem.list_tasks(r.key, "running")) + len(mem.list_tasks(r.key, "awaiting_approval"))
        done = len([t for t in mem.list_tasks(r.key, "done", limit=200)])
        last = mem.last_activity(r.key)
        last_s = last[11:16] if last else "-"
        state = "🟢 작업 중" if agent.busy else "⚪ 대기"
        lines.append(f"{r.emoji} {r.name}(#{r.channel}) {state} · 진행 {running} · 완료 {done} · "
                     f"토큰 {u['total']:,}/{budget:,} ({pct:.0f}%) · 최근 {last_s}")
    pend = mem.pending_approvals()
    if pend:
        lines.append("🔒 대기 중 승인: " + ", ".join(f"#{p['id']}({p['role']}/{p['tool']})" for p in pend))
    hand = mem.list_handoffs(limit=3)
    if hand:
        lines.append("📨 최근 넘김: " + " | ".join(f"{h['from_role']}→{h['to_role']} {h['summary'][:30]}" for h in hand))
    return "\n".join(lines)


def heartbeat_text(office: Office) -> str:
    return "💓 **살아있음** — 봇 7개 정상 가동 중\n" + compose_status(office)


def seconds_until(hour_kst: int, now: datetime | None = None) -> float:
    now = now or datetime.now(KST)
    target = now.replace(hour=hour_kst, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def heartbeat_loop(office: Office) -> None:
    channel = office.config.owner.heartbeat_channel
    hour = office.config.owner.heartbeat_hour_kst
    await office.say(channel, "🟢 사무실 가동 시작(프로세스 기동). 하루 1회 살아있음 알림을 보냅니다.")
    office.memory.log_event("manager", "heartbeat", "기동")
    while True:
        await asyncio.sleep(seconds_until(hour))
        office.memory.log_event("manager", "heartbeat", "일일 알림")
        await office.say(channel, heartbeat_text(office))


async def reminder_loop(office: Office, interval_sec: int = 60) -> None:
    while True:
        for r in office.memory.due_reminders(datetime.now(UTC).isoformat(timespec="seconds")):
            role = office.config.role(r["role"]) if r["role"] in office.agents else office.config.roles[0]
            await office.say(role.channel, f"⏰ **리마인더 #{r['id']}** {r['text']}")
            office.memory.mark_reminder(int(r["id"]))
        await asyncio.sleep(interval_sec)
