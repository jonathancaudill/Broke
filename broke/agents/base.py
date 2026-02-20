from __future__ import annotations

import json
import logging
from typing import Any

from broke.llm.provider import completion
from broke.tools.base import BaseTool

log = logging.getLogger(__name__)


class BaseAgent:
    """Async ReAct-style agent with a tool-calling loop.

    Subclasses set ``name``, ``description``, ``system_prompt``, and
    optionally override ``tools`` to equip the agent with capabilities.

    The class-level ``system_prompt`` serves as the hardcoded default.
    If a file exists at ``prompts/{name}.md`` it takes precedence (and
    can be hot-reloaded at runtime via ``/reload``).
    """

    name: str = "base"
    description: str = "A base agent."
    system_prompt: str = "You are a helpful assistant."
    max_iterations: int = 10

    def __init__(self) -> None:
        self._tools: list[BaseTool] = []

    def get_system_prompt(self) -> str:
        """Return the effective system prompt (file override or class default)."""
        from broke import prompts
        return prompts.agent_prompt(self.name, self.system_prompt)

    @property
    def tools(self) -> list[BaseTool]:
        return self._tools

    def register_tool(self, tool: BaseTool) -> None:
        self._tools.append(tool)

    def _tool_schemas(self) -> list[dict[str, Any]] | None:
        if not self._tools:
            return None
        return [t.to_openai_tool() for t in self._tools]

    def _find_tool(self, name: str) -> BaseTool | None:
        for t in self._tools:
            if t.name == name:
                return t
        return None

    async def _execute_tool_calls(
        self, tool_calls: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Execute tool calls and return message dicts for the conversation."""
        results: list[dict[str, Any]] = []
        for tc in tool_calls:
            tool = self._find_tool(tc["name"])
            if tool is None:
                output = f"Error: unknown tool '{tc['name']}'"
                log.debug("[%s] tool %s → NOT FOUND", self.name, tc["name"])
            else:
                log.debug(
                    "[%s] tool %s called with: %s",
                    self.name, tc["name"], json.dumps(tc["arguments"], indent=2),
                )
                try:
                    output = await tool.execute(**tc["arguments"])
                except Exception as exc:
                    output = f"Error executing {tc['name']}: {exc}"
                log.debug(
                    "[%s] tool %s returned: %s",
                    self.name, tc["name"], output[:500],
                )
            results.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": output,
            })
        return results

    async def run(self, query: str, context: dict[str, Any] | None = None) -> str:
        """Run the agent loop until the LLM produces a final text response."""
        log.debug("[%s] ── START ── query: %s", self.name, query[:200])

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.get_system_prompt()},
        ]
        if context and context.get("history"):
            messages.extend(context["history"])
        messages.append({"role": "user", "content": query})

        for iteration in range(self.max_iterations):
            resp = await completion(messages, tools=self._tool_schemas())

            if resp["tool_calls"]:
                log.debug(
                    "[%s] iteration %d → tool calls: %s",
                    self.name, iteration + 1,
                    [tc["name"] for tc in resp["tool_calls"]],
                )
                assistant_msg: dict[str, Any] = {"role": "assistant", "content": resp["content"]}
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"]),
                        },
                    }
                    for tc in resp["tool_calls"]
                ]
                messages.append(assistant_msg)

                tool_results = await self._execute_tool_calls(resp["tool_calls"])
                messages.extend(tool_results)
                continue

            final = resp["content"] or ""
            log.debug("[%s] ── DONE ── output: %s", self.name, final[:300])
            return final

        log.debug("[%s] ── DONE ── hit max iterations (%d)", self.name, self.max_iterations)
        return "I've reached my reasoning limit on this one. Here's what I have so far."
