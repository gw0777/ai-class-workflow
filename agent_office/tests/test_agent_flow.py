import asyncio

from agent_office.agent import build_system_prompt, extract_done_line
from agent_office.llm import FakeLLM
from agent_office.tools import safe_filename


def test_system_prompt_mentions_rules_and_colleagues(office_factory):
    office, _, _ = office_factory()
    p = build_system_prompt(office, office.config.role("research"))
    assert "특수체육" in p and "한 일:" in p and "매니저" in p and "#강의실" in p
    assert "적응체육'이라는 말은 절대" in p


def test_extract_done_line():
    assert extract_done_line("결과입니다\n\n한 일: 주제 3개 제안") == "주제 3개 제안"
    assert extract_done_line("📝 한 일: 끝냄") == "끝냄"
    assert extract_done_line("그냥 텍스트\n둘째 줄") == "그냥 텍스트"


def test_safe_filename_blocks_traversal():
    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename("강의계획서 3주차.md") == "강의계획서 3주차.md"
    assert safe_filename("a/b\\c;rm -rf.md") in ("c_rm -rf.md", "b_c_rm -rf.md")


def test_owner_request_with_tool_and_approval(office_factory):
    scripted = [
        FakeLLM.tool("write_file", {"filename": "협동학습_계획.md", "content": "적응체육 협동학습 계획"}, text="저장합니다"),
        FakeLLM.text("저장 완료했습니다.\n한 일: 협동학습 계획 파일 저장"),
    ]
    office, transport, llm = office_factory(scripted=scripted, auto_approve=True)

    async def go():
        handled = await office.handle_message(channel="강의실", author_id=4242, text="협동학습 수업 계획 만들어줘")
        assert handled
        await office.wait_idle()

    asyncio.run(go())
    texts = transport.texts("강의실")
    assert any("승인 요청 #1" in t and "write_file" in t for t in texts)
    assert any("한 일: 협동학습 계획 파일 저장" in t for t in texts)
    saved = office.settings.office_output_dir / "teaching" / "협동학습_계획.md"
    assert saved.read_text(encoding="utf-8") == "특수체육 협동학습 계획"   # 용어 자동 교정
    task = office.memory.list_tasks("teaching")[0]
    assert task["status"] == "done" and task["done_line"] == "협동학습 계획 파일 저장"
    assert office.memory.usage_today("teaching")["total"] == 300
    # 두 번째 호출에는 tool_result 가 들어가야 한다
    second = llm.calls[1]["messages"]
    assert second[-1]["content"][0]["type"] == "tool_result"
    assert "저장됨" in second[-1]["content"][0]["content"]
    assert llm.calls[0]["tools"][0]["strict"] is True


def test_denied_approval_stops_tool(office_factory):
    scripted = [
        FakeLLM.tool("send_email_draft", {"recipient": "x@y.z", "subject": "학회", "body": "안내"}),
        FakeLLM.text("승인되지 않아 중단합니다. 이유를 알려주세요.\n한 일: 메일 초안 승인 요청(거부됨)"),
    ]
    office, _transport, llm = office_factory(scripted=scripted, auto_approve=False)

    async def go():
        await office.handle_message(channel="학회", author_id=4242, text="학회 안내 메일 보내줘")
        await office.wait_idle()

    asyncio.run(go())
    assert office.memory.list_drafts() == []
    tool_result = llm.calls[1]["messages"][-1]["content"][0]["content"]
    assert "승인하지 않았습니다" in tool_result
    assert office.memory.get_approval(1)["status"] == "denied"


def test_approval_timeout_expires(office_factory):
    scripted = [FakeLLM.tool("write_file", {"filename": "a.md", "content": "x"}), FakeLLM.text("멈춤\n한 일: 대기")]
    office, transport, _ = office_factory(scripted=scripted, auto_approve=None, approval_timeout=0)

    async def go():
        await office.handle_message(channel="특강", author_id=4242, text="원고")
        await office.wait_idle()

    asyncio.run(go())
    assert office.memory.get_approval(1)["status"] == "expired"
    assert any("만료" in t for t in transport.texts("특강"))


def test_non_owner_ignored_and_bot_ignored(office_factory):
    office, transport, _ = office_factory()

    async def go():
        assert not await office.handle_message(channel="연구실", author_id=1, text="해줘")
        assert not await office.handle_message(channel="연구실", author_id=4242, text="해줘", author_is_bot=True)
        assert not await office.handle_message(channel="없는채널", author_id=4242, text="해줘")

    asyncio.run(go())
    assert transport.sent == []


def test_manager_delegates_to_research_channel(office_factory):
    scripted = [
        FakeLLM.tool("delegate", {"role": "research", "task": "특수체육 SEM 논문 초안",
                                  "done_criteria": "DOCX+유사도 리포트", "done_line": "요청을 연구 건으로 분류"}),
        FakeLLM.text("실장에게 넘겼습니다.\n한 일: 연구실로 위임"),
        FakeLLM.text("초안 작업 시작합니다.\n한 일: 논문 구조 설계"),
    ]
    office, transport, llm = office_factory(scripted=scripted)

    async def go():
        await office.handle_message(channel="매니저실", author_id=4242, text="SEM 논문 하나 써야 해")
        await office.wait_idle()

    asyncio.run(go())
    research_texts = transport.texts("연구실")
    assert any("넘김 #2" in t and "이렇게 되면 끝: DOCX+유사도 리포트" in t and "요청을 연구 건으로 분류" in t
               for t in research_texts)
    assert any("논문 구조 설계" in t for t in research_texts)
    h = office.memory.list_handoffs()[0]
    assert (h["from_role"], h["to_role"]) == ("manager", "research")
    t2 = office.memory.get_task(2)
    assert t2["origin"] == "handoff:manager" and t2["status"] == "done"
    # 넘겨받은 봇의 프롬프트에 완료 기준이 전달된다
    assert "[완료 기준] DOCX+유사도 리포트" in llm.calls[2]["messages"][0]["content"]
    assert office.memory.get_task(1)["done_line"] == "연구실로 위임"


def test_budget_exceeded_requires_override(office_factory):
    office, transport, llm = office_factory(scripted=[FakeLLM.text("ok\n한 일: 없음")], auto_approve=False, budget=100)
    office.memory.add_usage("secretary", "claude-sonnet-5-5", 90, 20)

    async def go():
        await office.handle_message(channel="비서실", author_id=4242, text="일정 정리")
        await office.wait_idle()

    asyncio.run(go())
    assert llm.calls == []
    assert any("예산 초과" in t for t in transport.texts("비서실"))
    assert office.memory.list_tasks("secretary")[0]["status"] == "blocked"


def test_subagent_uses_cheap_model(office_factory):
    scripted = [
        FakeLLM.tool("spawn_subagent", {"instruction": "요약해줘", "context": "긴 글", "model": ""}),
        FakeLLM.text("요약(팀원)"),
        FakeLLM.text("끝\n한 일: 팀원에게 요약 맡김"),
    ]
    office, _transport, llm = office_factory(scripted=scripted)

    async def go():
        await office.handle_message(channel="센터", author_id=4242, text="제안서 요약")
        await office.wait_idle()

    asyncio.run(go())
    assert llm.calls[1]["model"] == "claude-haiku-5-5" and llm.calls[1]["effort"] == "low"
    assert "요약(팀원)" in llm.calls[2]["messages"][-1]["content"][0]["content"]


def test_commands(office_factory):
    office, transport, _ = office_factory()

    async def go():
        await office.handle_message(channel="매니저실", author_id=4242, text="!상태")
        await office.handle_message(channel="매니저실", author_id=4242, text="!승인 99")
        await office.handle_message(channel="매니저실", author_id=4242, text="!도움말")

    asyncio.run(go())
    texts = transport.texts("매니저실")
    assert "사무실 상태" in texts[0] and all(r.name in texts[0] for r in office.config.roles)
    assert "대기 중인 승인이 아니거나" in texts[1]
    assert "!승인 N" in texts[2]


def test_refusal_is_reported(office_factory):
    from agent_office.llm import LLMResponse, Usage
    refusal = LLMResponse(text="", tool_calls=[], stop_reason="refusal", usage=Usage(5, 0), model="fake",
                          content=[], refusal_category="general_harms")
    office, transport, _ = office_factory(scripted=[refusal])

    async def go():
        await office.handle_message(channel="특강", author_id=4242, text="x")
        await office.wait_idle()

    asyncio.run(go())
    assert any("거절" in t for t in transport.texts("특강"))
    assert office.memory.list_tasks("writer")[0]["status"] == "failed"
