from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

from broke.agents.base import BaseAgent
from broke.tools.call_agent import CallAgentTool
from broke.tools.rag_query import RAGQueryTool

log = logging.getLogger(__name__)

_INSTRUCTIONS = """\

---

## Instructions

You have direct access to Jonathan's knowledge base via the **rag_query** tool. \
Use it to look up accurate information before answering questions about his \
skills, experience, projects, and background. You can search specific \
collections (resume, projects, skills, background) or all of them at once.

For tasks that go beyond simple retrieval, call a specialist agent:
- **scheduling** — Check availability and arrange meetings with Jonathan.
- **researcher** — Search the web for current or external information.
- **deep_rag** — Thorough, multi-pass retrieval for complex questions that \
need cross-referencing or exhaustive coverage.

Always query the knowledge base before making claims about Jonathan. \
If the knowledge base doesn't have the answer, say so honestly.

**Important — conversational flow:** When you need to use a tool, ALWAYS \
include a brief, natural acknowledgment in your response text alongside the \
tool call. Something like "sure, let me pull that up" or "on it — one sec." \
Stay in character. This text will be shown to the user immediately while the \
tool runs, so it keeps the conversation feeling alive. Never call tools \
silently with no accompanying text.
"""


class Orchestrator(BaseAgent):
    """Streaming ReAct orchestrator.

    Runs a tool-calling loop — queries RAG directly, calls specialist
    agents when needed — and streams the final response token-by-token.
    """

    name = "orchestrator"
    description = "The central agent that answers questions and delegates to specialists."
    system_prompt = ""
    max_iterations = 12

    def __init__(self) -> None:
        super().__init__()
        self.register_tool(RAGQueryTool())
        self.register_tool(CallAgentTool())

    def _build_system_prompt(self) -> str:
        from broke import prompts
        return prompts.personality() + _INSTRUCTIONS

    async def run_stream(
        self, query: str, context: dict[str, Any] | None = None, *, debug: bool = False,
    ) -> AsyncIterator[dict[str, Any]]:
        """Streaming ReAct loop. Yields event dicts for the terminal renderer."""
        from broke.llm.provider import stream_completion_with_tools

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._build_system_prompt()},
        ]
        if context and context.get("history"):
            messages.extend(context["history"][-6:])
        messages.append({"role": "user", "content": query})

        for iteration in range(self.max_iterations):
            log.debug("[orchestrator] iteration %d", iteration + 1)

            full_content = ""
            final_event: dict[str, Any] | None = None

            async for event in stream_completion_with_tools(
                messages, tools=self._tool_schemas()
            ):
                if event["type"] == "token":
                    full_content += event["content"]
                    yield {"type": "token", "content": event["content"]}
                elif event["type"] in ("done", "tool_calls"):
                    final_event = event

            if final_event is None:
                yield {"type": "final", "content": full_content or ""}
                return

            if final_event["type"] == "done":
                yield {"type": "final", "content": final_event["content"]}
                return

            # --- Tool calls: execute and loop ---
            tool_calls = final_event["calls"]
            tool_names = [tc["name"] for tc in tool_calls]
            log.debug("[orchestrator] tool calls: %s", tool_names)

            if full_content:
                yield {"type": "ack_break"}

            yield {
                "type": "status",
                "content": self._describe_tool_calls(tool_calls),
            }

            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": final_event.get("content"),
            }
            assistant_msg["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["arguments"]),
                    },
                }
                for tc in tool_calls
            ]
            messages.append(assistant_msg)

            if debug:
                for tc in tool_calls:
                    args_str = json.dumps(tc["arguments"], default=str)
                    if len(args_str) > 200:
                        args_str = args_str[:200] + "..."
                    yield {
                        "type": "agent_tool_call",
                        "agent": "orchestrator",
                        "tool": tc["name"],
                        "args": tc["arguments"],
                    }

            tool_results = await self._execute_tool_calls(tool_calls)
            messages.extend(tool_results)

            if debug:
                for tr in tool_results:
                    content = tr.get("content", "")
                    if len(content) > 300:
                        content = content[:300] + "..."
                    yield {
                        "type": "agent_tool_result",
                        "agent": "orchestrator",
                        "content": content,
                    }

        yield {
            "type": "final",
            "content": "i hit my reasoning limit on this one — try asking in a different way?",
        }

    async def run(self, query: str, context: dict[str, Any] | None = None) -> str:
        """Non-streaming fallback — collects the final content from the stream."""
        final = ""
        async for msg in self.run_stream(query, context):
            if msg["type"] == "final":
                final = msg.get("content", "")
        return final

    @staticmethod
    def _describe_tool_calls(tool_calls: list[dict[str, Any]]) -> str:
        parts = []
        for tc in tool_calls:
            name = tc["name"]
            if name == "rag_query":
                coll = tc.get("arguments", {}).get("collection", "all")
                parts.append(f"searching knowledge base ({coll})")
            elif name == "call_agent":
                agent = tc.get("arguments", {}).get("agent_name", "?")
                parts.append(f"talking to {agent}")
            else:
                parts.append(name)
        return ", ".join(parts) + "..."
