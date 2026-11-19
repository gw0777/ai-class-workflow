"""Claude 호출 래퍼.

- 공식 anthropic SDK(AsyncAnthropic) 사용. 모델별로 adaptive thinking + output_config.effort.
- Opus 5.5 / Sonnet 5.5 / Fable 계열에는 서버측 refusal 폴백(fallbacks="default")을 기본 적용.
- 테스트와 배선 점검을 위해 같은 인터페이스의 FakeLLM / EchoLLM을 둔다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol

FALLBACK_BETA = "server-side-fallback-2026-07-01"
FALLBACK_MODEL_PREFIXES = ("claude-opus-5-5", "claude-sonnet-5-5", "claude-fable-5", "claude-opus-5")


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[ToolCall]
    stop_reason: str
    usage: Usage
    model: str
    content: Any = field(default=None)      # 원본 content 블록(assistant 턴으로 되돌려 보낼 때 사용)
    refusal_category: str | None = None


class LLM(Protocol):
    async def complete(self, *, model: str, system: str, messages: list[dict[str, Any]],
                       tools: list[dict[str, Any]] | None, effort: str, max_tokens: int) -> LLMResponse: ...


def _normalize(response: Any, model: str) -> LLMResponse:
    text_parts: list[str] = []
    calls: list[ToolCall] = []
    for block in response.content:
        btype = getattr(block, "type", None)
        if btype == "text":
            text_parts.append(block.text)
        elif btype == "tool_use":
            raw = block.input
            if isinstance(raw, str):            # 방어: 문자열로 오면 json.loads
                raw = json.loads(raw)
            calls.append(ToolCall(id=block.id, name=block.name, input=dict(raw or {})))
    usage = getattr(response, "usage", None)
    u = Usage(
        input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
        output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
        cache_read_tokens=int(getattr(usage, "cache_read_input_tokens", 0) or 0),
    )
    category = None
    stop = getattr(response, "stop_reason", "end_turn") or "end_turn"
    details = getattr(response, "stop_details", None)
    if stop == "refusal" and details is not None:
        category = getattr(details, "category", None)
    return LLMResponse(text="\n".join(text_parts).strip(), tool_calls=calls, stop_reason=stop, usage=u,
                       model=getattr(response, "model", model), content=response.content,
                       refusal_category=category)


class AnthropicLLM:
    """실제 Claude API 호출."""

    def __init__(self, api_key: str | None = None, enable_fallbacks: bool = True, timeout: float = 600.0) -> None:
        from anthropic import (
            AsyncAnthropic,  # 지연 import: 테스트에서 SDK 없이도 모듈 로드 가능
        )

        self._client = AsyncAnthropic(api_key=api_key or None, timeout=timeout, max_retries=2)
        self.enable_fallbacks = enable_fallbacks

    async def complete(self, *, model: str, system: str, messages: list[dict[str, Any]],
                       tools: list[dict[str, Any]] | None, effort: str, max_tokens: int) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            # 시스템 프롬프트는 고정 → 캐시 브레이크포인트. 변하는 내용은 messages 뒤쪽에 둔다.
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            "messages": messages,
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": effort},
        }
        if tools:
            kwargs["tools"] = tools
        use_fallback = self.enable_fallbacks and model.startswith(FALLBACK_MODEL_PREFIXES)
        if use_fallback:
            response = await self._client.beta.messages.create(
                betas=[FALLBACK_BETA], fallbacks="default", **kwargs)
        else:
            response = await self._client.messages.create(**kwargs)
        return _normalize(response, model)


class EchoLLM:
    """DRY_RUN: API 호출 없이 입력을 되돌려 준다(배선·권한·채널 점검용)."""

    async def complete(self, *, model: str, system: str, messages: list[dict[str, Any]],
                       tools: list[dict[str, Any]] | None, effort: str, max_tokens: int) -> LLMResponse:
        last = messages[-1]["content"] if messages else ""
        if not isinstance(last, str):
            last = json.dumps(last, ensure_ascii=False)[:300]
        return LLMResponse(text=f"[DRY_RUN:{model}] {last}", tool_calls=[], stop_reason="end_turn",
                           usage=Usage(10, 10), model=model, content=[{"type": "text", "text": last}])


class FakeLLM:
    """테스트용: 미리 정해둔 응답을 순서대로 돌려준다."""

    def __init__(self, scripted: list[LLMResponse] | None = None) -> None:
        self.scripted = list(scripted or [])
        self.calls: list[dict[str, Any]] = []

    @staticmethod
    def text(text: str, model: str = "fake", usage: tuple[int, int] = (100, 50)) -> LLMResponse:
        return LLMResponse(text=text, tool_calls=[], stop_reason="end_turn",
                           usage=Usage(*usage), model=model, content=[{"type": "text", "text": text}])

    @staticmethod
    def tool(name: str, inp: dict[str, Any], call_id: str = "toolu_1", text: str = "",
             usage: tuple[int, int] = (100, 50)) -> LLMResponse:
        content: list[dict[str, Any]] = []
        if text:
            content.append({"type": "text", "text": text})
        content.append({"type": "tool_use", "id": call_id, "name": name, "input": inp})
        return LLMResponse(text=text, tool_calls=[ToolCall(call_id, name, inp)], stop_reason="tool_use",
                           usage=Usage(*usage), model="fake", content=content)

    async def complete(self, **kwargs: Any) -> LLMResponse:
        self.calls.append(kwargs)
        if not self.scripted:
            return self.text("(응답 없음)")
        return self.scripted.pop(0)
