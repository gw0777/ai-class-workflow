from agent_office.memory import Memory


def test_tasks_usage_approvals_roundtrip():
    m = Memory(":memory:")
    tid = m.create_task("research", "연구실", "논문 주제 제안", "주제 3개", "owner")
    m.update_task(tid, status="done", done_line="주제 3개 제안함")
    t = m.get_task(tid)
    assert t["status"] == "done" and t["done_line"] == "주제 3개 제안함"
    assert m.list_tasks("research", "done")[0]["id"] == tid

    m.add_usage("research", "claude-opus-5-5", 1000, 200, 300)
    m.add_usage("research", "claude-haiku-5-5", 10, 5)
    u = m.usage_today("research")
    assert u == {"input": 1010, "output": 205, "cache_read": 300, "total": 1215}
    assert m.usage_by_role_today()["research"]["total"] == 1215

    aid = m.create_approval("research", tid, "write_file", "파일 저장", {"filename": "a.md"}, "연구실")
    m.set_approval_message(aid, "m99")
    assert m.find_approval_by_message("m99")["id"] == aid
    assert len(m.pending_approvals()) == 1
    m.resolve_approval(aid, "approved")
    assert m.find_approval_by_message("m99") is None
    assert m.get_approval(aid)["status"] == "approved"

    hid = m.log_handoff("manager", "research", tid, "논문", "요청 분류함", "DOCX 생성")
    assert m.list_handoffs()[0]["id"] == hid
    m.log_event("manager", "handoff", "→ research")
    assert m.last_activity("manager") is not None
    assert m.recent_events(5)[0]["kind"] == "handoff"

    rid = m.add_reminder("secretary", "2000-01-01T00:00:00+00:00", "과거 리마인더")
    assert m.due_reminders()[0]["id"] == rid
    m.mark_reminder(rid)
    assert m.due_reminders() == []
    did = m.add_draft("society", "email", "본문", "a@b.c", "제목")
    assert m.list_drafts()[0]["id"] == did
