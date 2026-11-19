from pathlib import Path

from agent_office.config import (
    DEFAULT_AGENTS_YAML,
    Settings,
    enforce_terms,
    load_office_config,
)


def test_seven_roles_with_unique_channels():
    cfg = load_office_config(DEFAULT_AGENTS_YAML)
    assert len(cfg.roles) == 7
    assert {r.key for r in cfg.roles} == {"manager", "research", "teaching", "society", "center", "writer", "secretary"}
    assert len({r.channel for r in cfg.roles}) == 7
    assert cfg.role("manager").tools and "delegate" in cfg.role("manager").tools


def test_models_are_official_ids_without_date_suffix():
    cfg = load_office_config(DEFAULT_AGENTS_YAML)
    for r in cfg.roles:
        m = cfg.model_for(r)
        assert m.startswith("claude-")
        assert not m[-8:].isdigit(), f"날짜 접미사 금지: {m}"
    assert cfg.defaults.subagent_model == "claude-haiku-5-5"


def test_terminology_rule():
    assert enforce_terms("적응체육과 적응 체육") == "특수체육과 특수체육"
    text = Path(DEFAULT_AGENTS_YAML).read_text(encoding="utf-8")
    # 설정 파일 안에서도 금지 용어는 규칙 설명 문장에만 나와야 한다
    assert "특수체육" in text
    for line in text.splitlines():
        if "적응체육" in line or "적응 체육" in line:
            assert "사용하지 않는다" in line or "#" in line


def test_owner_env_override(monkeypatch):
    s = Settings(_env_file=None, owner_discord_id=777)
    cfg = load_office_config(DEFAULT_AGENTS_YAML, s)
    assert cfg.owner.discord_id == 777
    monkeypatch.setenv("DISCORD_TOKEN_RESEARCH", "tok-r")
    s2 = Settings(_env_file=None, discord_token="shared")
    assert s2.role_token("research") == "tok-r"
    assert s2.role_token("manager") == "shared"
