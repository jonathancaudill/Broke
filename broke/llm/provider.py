from __future__ import annotations

import json
import logging
from typing import Any

import litellm

from broke.config import get_settings

litellm.drop_params = True
log = logging.getLogger(__name__)


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
