from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import litellm

from broke.config import get_settings

litellm.drop_params = True
log = logging.getLogger(__name__)

# Runtime-mutable reasoning effort: "none" | "low" | "medium" | "high" | None
# None = don't send the param (let the API decide).
_reasoning_effort: str | None = None

VALID_REASONING_EFFORTS = ("minimal", "low", "medium", "high")


def set_reasoning_effort(level: str | None) -> str | None:
    """Set reasoning effort globally. Returns the new value."""
    global _reasoning_effort
    if level is not None and level not in VALID_REASONING_EFFORTS:
        raise ValueError(f"Invalid reasoning effort: {level!r}. Choose from {VALID_REASONING_EFFORTS}")
    _reasoning_effort = level
    return _reasoning_effort


def get_reasoning_effort() -> str | None:
    return _reasoning_effort


async def completion(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Unified async LLM completion via litellm.

    Returns a normalised dict:
        {
            "content": str | None,
            "tool_calls": list[dict] | None,   # [{id, name, arguments}]
            "raw": ModelResponse,
        }
    """
    settings = get_settings()
    model = model or settings.model

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "timeout": timeout,
    }
    if settings.llm_base_url:
        kwargs["api_base"] = settings.llm_base_url
    if tools:
        kwargs["tools"] = tools
    if _reasoning_effort is not None:
        kwargs["reasoning_effort"] = _reasoning_effort

    last_user = next(
        (m["content"][:150] for m in reversed(messages) if m["role"] == "user"), "—",
    )
    log.debug(
        "LLM request: model=%s msgs=%d tools=%s | user: %s",
        model, len(messages), bool(tools), last_user,
    )
    response = await litellm.acompletion(**kwargs)
    choice = response.choices[0]
    message = choice.message
    log.debug(
        "LLM response: %d chars, tool_calls=%s, finish=%s",
        len(message.content or ""), bool(message.tool_calls), choice.finish_reason,
    )

    tool_calls = None
    if message.tool_calls:
        tool_calls = []
        for tc in message.tool_calls:
            args = tc.function.arguments
            if isinstance(args, str):
                args = json.loads(args)
            tool_calls.append({
                "id": tc.id,
                "name": tc.function.name,
                "arguments": args,
            })

    return {
        "content": message.content,
        "tool_calls": tool_calls,
        "raw": response,
    }


async def stream_completion(
    messages: list[dict[str, Any]],
    model: str | None = None,
    temperature: float = 0.7,
    timeout: float = 120.0,
) -> AsyncIterator[str]:
    """Streaming variant — yields content tokens as they arrive.

    No tool support; intended for direct chat / personality testing.
    """
    settings = get_settings()
    model = model or settings.model

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "timeout": timeout,
        "stream": True,
    }
    if settings.llm_base_url:
        kwargs["api_base"] = settings.llm_base_url
    if _reasoning_effort is not None:
        kwargs["reasoning_effort"] = _reasoning_effort

    log.debug("LLM stream request: model=%s msgs=%d effort=%s", model, len(messages), _reasoning_effort)
    response = await litellm.acompletion(**kwargs)

    async for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


async def stream_completion_with_tools(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    timeout: float = 120.0,
) -> AsyncIterator[dict[str, Any]]:
    """Streaming completion that handles both content and tool calls.

    Yields events as they arrive:
      - ``{"type": "token", "content": str}`` for each content delta
      - ``{"type": "done", "content": str}`` when the response is pure content
      - ``{"type": "tool_calls", "calls": [...], "content": str | None}``
        when the model wants to invoke tools

    The caller can inspect the final event to decide whether to execute
    tool calls and loop, or treat the content as the finished answer.
    """
    settings = get_settings()
    model = model or settings.model

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "timeout": timeout,
        "stream": True,
    }
    if settings.llm_base_url:
        kwargs["api_base"] = settings.llm_base_url
    if tools:
        kwargs["tools"] = tools
    if _reasoning_effort is not None:
        kwargs["reasoning_effort"] = _reasoning_effort

    log.debug(
        "LLM stream+tools request: model=%s msgs=%d tools=%s effort=%s",
        model, len(messages), bool(tools), _reasoning_effort,
    )
    response = await litellm.acompletion(**kwargs)

    full_content = ""
    tool_call_buffers: dict[int, dict[str, Any]] = {}

    async for chunk in response:
        delta = chunk.choices[0].delta

        if delta.content:
            full_content += delta.content
            yield {"type": "token", "content": delta.content}

        if delta.tool_calls:
            for tc_delta in delta.tool_calls:
                idx = tc_delta.index
                if idx not in tool_call_buffers:
                    tool_call_buffers[idx] = {
                        "id": tc_delta.id or "",
                        "name": "",
                        "arguments": "",
                    }
                buf = tool_call_buffers[idx]
                if tc_delta.id:
                    buf["id"] = tc_delta.id
                if tc_delta.function:
                    if tc_delta.function.name:
                        buf["name"] += tc_delta.function.name
                    if tc_delta.function.arguments:
                        buf["arguments"] += tc_delta.function.arguments

    if tool_call_buffers:
        calls = []
        for idx in sorted(tool_call_buffers):
            buf = tool_call_buffers[idx]
            try:
                args = json.loads(buf["arguments"])
            except json.JSONDecodeError:
                args = {}
            calls.append({
                "id": buf["id"],
                "name": buf["name"],
                "arguments": args,
            })
        log.debug("LLM stream produced %d tool call(s): %s", len(calls), [c["name"] for c in calls])
        yield {"type": "tool_calls", "calls": calls, "content": full_content or None}
    else:
        log.debug("LLM stream done: %d chars content", len(full_content))
        yield {"type": "done", "content": full_content}
