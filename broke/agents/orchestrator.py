from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

from broke.agents.base import BaseAgent
from broke.events.bus import EventBus
from broke.llm.provider import completion

log = logging.getLogger(__name__)

# Templates are split from personality so personality can be hot-reloaded.
# {personality} is injected at call time via _build_routing_prompt / _build_synthesis_prompt.

_ROUTING_INSTRUCTIONS = """\

---

## Routing Instructions

You are the routing brain of this system. Given the user's message, decide \
which specialist agents should be called to answer it. You may call zero \
agents (if you can handle it yourself), one, or multiple in parallel.

Available specialists:
- skills: Technical abilities, programming languages, frameworks, tools
- experience: Work history, roles, achievements, career
- projects: Things Jonathan has built, project details, tech stacks
- culture: Work style, personality, values, team fit

Respond with a JSON object (no markdown fences):
{
  "acknowledgment": "A brief, natural sentence acknowledging the user's question — stay in character per the personality guide above.",
  "agents": [
    {"agent": "<agent_name>", "query": "<reframed query for that specialist>"}
  ],
  "direct_answer": null
}

If you can answer directly without any specialists (e.g. greetings, meta \
questions about yourself), set "agents" to [] and put your answer in \
"direct_answer". Keep the personality guide in mind for direct answers too.
"""

_SYNTHESIS_INSTRUCTIONS = """\

---

## Synthesis Instructions

You've just received information from your specialist agents. Synthesize \
their findings into a single, polished response for the user.

Specialist results:
{results}

Original question: {query}

Compose a cohesive, engaging response. Don't say "according to the skills \
agent" — just weave the information naturally. If results are thin, be \
honest about it rather than making things up. Stay in character at all times.
"""


class Orchestrator(BaseAgent):
    """Async conversational orchestrator.

    Unlike specialist agents that return a single string, the orchestrator
    *yields* intermediate and final messages so the terminal can stream
    them in real time.
    """

    name = "orchestrator"
    description = "The conversational orchestrator that routes queries to specialists."
    system_prompt = ""  # Uses specialised prompts per phase

    def __init__(self) -> None:
        super().__init__()
        self.event_bus = EventBus()

    # --- Prompt builders (read personality fresh from cache) -----------

    @staticmethod
    def _build_routing_prompt() -> str:
        from broke import prompts
        return prompts.personality() + _ROUTING_INSTRUCTIONS

    @staticmethod
    def _build_synthesis_prompt(results_text: str, query: str) -> str:
        from broke import prompts
        return prompts.personality() + _SYNTHESIS_INSTRUCTIONS.format(
            results=results_text, query=query,
        )

    async def run_stream(
        self, query: str, context: dict[str, Any] | None = None, *, debug: bool = False,
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield message dicts: {"type": "ack"|"status"|"final", "content": str}."""

        # --- Phase 1: Route ---
        plan = await self._plan_dispatch(query, context)

        if plan.get("direct_answer"):
            yield {"type": "synthesis_start"}
            full_text = ""
            async for token in self._stream_direct(plan["direct_answer"]):
                full_text += token
                yield {"type": "token", "content": token}
            yield {"type": "final", "content": full_text}
            return

        ack = plan.get("acknowledgment", "Let me look into that.")
        yield {"type": "ack", "content": ack}

        tasks = plan.get("agents", [])
        if not tasks:
            yield {"type": "final", "content": ack}
            return

        # --- Phase 2: Dispatch ---
        if debug:
            for t in tasks:
                yield {
                    "type": "agent_input",
                    "agent": t["agent"],
                    "query": t["query"],
                }

        pending = await self.event_bus.dispatch_all(tasks)
        collected: list[tuple[str, str]] = []

        yield {
            "type": "status",
            "content": f"Checking with {', '.join(t['agent'] for t in tasks)}...",
        }

        # --- Phase 3: Collect results ---
        while pending:
            done, pending = await self.event_bus.wait_next(pending)
            collected.extend(done)

            if debug:
                for agent_name, result in done:
                    yield {
                        "type": "agent_output",
                        "agent": agent_name,
                        "content": result,
                    }

            if pending:
                still = [at.agent_name for at in pending]
                yield {
                    "type": "status",
                    "content": f"Still waiting on {', '.join(still)}...",
                }

        # --- Phase 4: Synthesise (streamed) ---
        yield {"type": "synthesis_start"}
        full_text = ""
        async for token in self._synthesise_stream(query, collected, context):
            full_text += token
            yield {"type": "token", "content": token}
        yield {"type": "final", "content": full_text, "sources": [c[0] for c in collected]}

    async def run(self, query: str, context: dict[str, Any] | None = None) -> str:
        """Non-streaming fallback — collects the final content from the stream."""
        final = ""
        async for msg in self.run_stream(query, context):
            if msg["type"] == "final":
                final = msg.get("content", "")
        return final

    async def _plan_dispatch(
        self, query: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        log.debug("[orchestrator] routing query: %s", query[:200])
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._build_routing_prompt()},
        ]
        if context and context.get("history"):
            messages.extend(context["history"][-6:])
        messages.append({"role": "user", "content": query})

        resp = await completion(messages, temperature=0.3)
        raw = resp["content"] or "{}"

        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]

        try:
            plan = json.loads(raw)
        except json.JSONDecodeError:
            log.warning("Orchestrator routing returned invalid JSON: %s", raw[:200])
            return {
                "acknowledgment": "Hmm, let me think about that...",
                "agents": [{"agent": "skills", "query": query}],
                "direct_answer": None,
            }

        agents = [t["agent"] for t in plan.get("agents", [])]
        if plan.get("direct_answer"):
            log.debug("[orchestrator] routing decision: direct answer")
        else:
            log.debug("[orchestrator] routing decision: dispatch → %s", agents)
        return plan

    async def _synthesise_stream(
        self,
        query: str,
        results: list[tuple[str, str]],
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Streaming synthesis — yields tokens as they arrive."""
        from broke.llm.provider import stream_completion

        for agent_name, result in results:
            log.debug(
                "[orchestrator] specialist result from '%s': %s",
                agent_name, result[:300],
            )

        results_text = "\n\n".join(
            f"[{agent_name}]:\n{result}" for agent_name, result in results
        )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._build_synthesis_prompt(results_text, query)},
        ]
        if context and context.get("history"):
            messages.extend(context["history"][-4:])
        messages.append({
            "role": "user",
            "content": f"Synthesise a response to: {query}",
        })

        log.debug("[orchestrator] streaming synthesis from %d specialist results", len(results))
        async for token in stream_completion(messages, temperature=0.7):
            yield token

    async def _stream_direct(self, prefab_answer: str) -> AsyncIterator[str]:
        """Yield a pre-fabricated direct answer through the token pipeline."""
        yield prefab_answer
