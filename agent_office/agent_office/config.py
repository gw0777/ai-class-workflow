"""설정 로딩: 환경변수(.env) + config/agents.yaml."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_DIR = Path(__file__).resolve().parent
BASE_DIR = PACKAGE_DIR.parent
REPO_DIR = BASE_DIR.parent
DEFAULT_AGENTS_YAML = BASE_DIR / "config" / "agents.yaml"

FORBIDDEN_TERMS = {"적응체육": "특수체육", "적응 체육": "특수체육"}


def enforce_terms(text: str) -> str:
    """용어 통일: '적응체육/적응 체육' → '특수체육'."""
    for bad, good in FORBIDDEN_TERMS.items():
        text = text.replace(bad, good)
    return text


class Settings(BaseSettings):
    """환경변수 기반 런타임 설정."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    discord_token: str = ""                 # 모든 역할이 공유하는 봇 토큰(없으면 역할별 토큰 사용)
    owner_discord_id: int = 0               # 승인 권한자
    agents_yaml: Path = DEFAULT_AGENTS_YAML
    office_db: Path = BASE_DIR / "office.db"
    office_output_dir: Path = BASE_DIR / "output"
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8787
    paper_pipeline_url: str = "http://localhost:8000"
    paper_pipeline_api_key: str = ""
    approval_timeout_sec: int = 86400
    heartbeat_enabled: bool = True
    enable_fallbacks: bool = True           # 서버측 refusal 폴백(opus/sonnet 5.5 계열)
    allow_non_owner: bool = False           # 소유자 외 사용자의 요청 허용 여부
    dry_run: bool = False                   # LLM 호출 없이 에코(배선 점검용)

    def role_token(self, role_key: str) -> str:
        """역할별 토큰(DISCORD_TOKEN_<KEY>)이 있으면 우선, 없으면 공유 토큰."""
        return os.getenv(f"DISCORD_TOKEN_{role_key.upper()}", "") or self.discord_token


class OwnerConfig(BaseModel):
    discord_id: int = 0
    display_name: str = "교수님"
    heartbeat_channel: str = "사무실"
    heartbeat_hour_kst: int = 8


class DefaultsConfig(BaseModel):
    model: str = "claude-opus-5-5"
    effort: str = "high"
    max_tokens: int = 16000
    daily_token_budget: int = 2_000_000
    subagent_model: str = "claude-haiku-5-5"
    subagent_effort: str = "low"
    approval_required_tools: list[str] = Field(default_factory=list)


class RoleConfig(BaseModel):
    key: str
    name: str
    title: str
    channel: str
    emoji: str = "🤖"
    model: str | None = None
    effort: str | None = None
    max_tokens: int | None = None
    daily_token_budget: int | None = None
    tools: list[str] = Field(default_factory=list)
    purpose: str = ""
    done_criteria: str = ""

    @field_validator("purpose", "done_criteria", "title")
    @classmethod
    def _terms(cls, v: str) -> str:
        return enforce_terms(v.strip())


class OfficeConfig(BaseModel):
    owner: OwnerConfig = Field(default_factory=OwnerConfig)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    roles: list[RoleConfig]

    @field_validator("roles")
    @classmethod
    def _unique(cls, roles: list[RoleConfig]) -> list[RoleConfig]:
        keys = [r.key for r in roles]
        channels = [r.channel for r in roles]
        if len(set(keys)) != len(keys):
            raise ValueError("역할 key가 중복됩니다")
        if len(set(channels)) != len(channels):
            raise ValueError("채널 이름이 중복됩니다 (채널 1개 = 봇 1개)")
        return roles

    # 편의 접근자 -------------------------------------------------------
    def role(self, key: str) -> RoleConfig:
        for r in self.roles:
            if r.key == key:
                return r
        raise KeyError(key)

    def role_by_channel(self, channel: str) -> RoleConfig | None:
        for r in self.roles:
            if r.channel == channel:
                return r
        return None

    def model_for(self, role: RoleConfig) -> str:
        return role.model or self.defaults.model

    def effort_for(self, role: RoleConfig) -> str:
        return role.effort or self.defaults.effort

    def max_tokens_for(self, role: RoleConfig) -> int:
        return role.max_tokens or self.defaults.max_tokens

    def budget_for(self, role: RoleConfig) -> int:
        return role.daily_token_budget or self.defaults.daily_token_budget

    def requires_approval(self, tool_name: str) -> bool:
        return tool_name in self.defaults.approval_required_tools


def load_office_config(path: Path | str | None = None, settings: Settings | None = None) -> OfficeConfig:
    p = Path(path) if path else DEFAULT_AGENTS_YAML
    data: dict[str, Any] = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    cfg = OfficeConfig.model_validate(data)
    owner_env = (settings.owner_discord_id if settings else 0) or int(os.getenv("OWNER_DISCORD_ID", "0") or 0)
    if owner_env:
        cfg.owner.discord_id = owner_env
    return cfg
