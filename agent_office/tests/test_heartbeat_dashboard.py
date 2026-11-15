import asyncio
from datetime import datetime

from fastapi.testclient import TestClient

from agent_office.dashboard import create_app
from agent_office.heartbeat import (
    KST,
    compose_status,
    heartbeat_text,
    reminder_loop,
    seconds_until,
)


def test_seconds_until_next_hour():
    now = datetime(2026, 11, 15, 7, 30, tzinfo=KST)
    assert seconds_until(8, now) == 1800
    assert seconds_until(7, now) == 23.5 * 3600


def test_status_and_heartbeat_text(office_factory):
    office, _, _ = office_factory()
    office.memory.add_usage("research", "claude-opus-5-5", 1000, 500)
    office.memory.create_approval("research", None, "write_file", "저장", {}, "연구실")
    s = compose_status(office)
    assert "실장(#연구실)" in s and "1,500" in s and "대기 중 승인: #1" in s
    assert heartbeat_text(office).startswith("💓")


def test_reminder_delivery(office_factory):
    office, transport, _ = office_factory()
    office.memory.add_reminder("secretary", "2000-01-01T00:00:00+00:00", "학회 등록 마감")

    async def go():
        task = asyncio.create_task(reminder_loop(office, interval_sec=60))
        await asyncio.sleep(0.05)
        task.cancel()

    asyncio.run(go())
    assert any("리마인더 #1" in t and "학회 등록 마감" in t for t in transport.texts("비서실"))


def test_dashboard_endpoints(office_factory):
    office, _, _ = office_factory()
    aid = office.memory.create_approval("center", None, "write_file", "저장", {}, "센터")
    client = TestClient(create_app(office))
    assert client.get("/healthz").json() == {"ok": True, "roles": 7}
    assert "사무실 화면" in client.get("/").text
    data = client.get("/api/status").json()
    assert len(data["roles"]) == 7 and data["roles"][0]["key"] == "manager"
    assert data["pending_approvals"][0]["id"] == aid
    assert client.post(f"/api/approvals/{aid}/approve").json()["ok"] is True
    assert office.memory.get_approval(aid)["status"] == "approved"
    assert client.post(f"/api/approvals/{aid}/approve").status_code == 404
    assert client.post(f"/api/approvals/{aid}/maybe").status_code == 400
    assert client.get("/api/tasks").json() == []
