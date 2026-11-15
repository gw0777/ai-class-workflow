import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from agent_office.config import Settings, load_office_config
from agent_office.llm import FakeLLM
from agent_office.memory import Memory
from agent_office.office import Office
from agent_office.transport import FakeTransport

OWNER = 4242


def make_office(tmp_path, scripted=None, auto_approve=True, approval_timeout=5, budget=None):
    settings = Settings(_env_file=None, anthropic_api_key="test", owner_discord_id=OWNER,
                        office_output_dir=tmp_path / "out", office_db=tmp_path / "office.db",
                        approval_timeout_sec=approval_timeout)
    config = load_office_config(settings.agents_yaml, settings)
    if budget is not None:
        config.defaults.daily_token_budget = budget
        for r in config.roles:
            r.daily_token_budget = None
    transport = FakeTransport()
    llm = FakeLLM(scripted or [])
    office = Office(config=config, settings=settings, memory=Memory(settings.office_db), transport=transport, llm=llm)

    if auto_approve is not None:
        async def auto(message_id):
            rec = office.memory.find_approval_by_message(message_id)
            if rec:
                office.gate.resolve(int(rec["id"]), auto_approve, OWNER)
        transport.on_approval_request = auto
    settings.office_output_dir.mkdir(parents=True, exist_ok=True)
    return office, transport, llm


@pytest.fixture
def office_factory(tmp_path):
    return lambda **kw: make_office(tmp_path, **kw)
