from __future__ import annotations

from typing import Any

from broke.agents.registry import registry
from broke.tools.base import BaseTool


class CallAgentTool(BaseTool):
    """Lets one agent invoke another agent by name (peer-to-peer)."""

    @property
    def name(self) -> str:
        return "call_agent"

    @property
    def description(self) -> str:
        available = registry.list_agents()
        agent_list = ", ".join(a["name"] for a in available) if available else "(none)"
        return (
            "Call another specialist agent to get information or a second opinion. "
            f"Available agents: {agent_list}"
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "agent_name": {
                "type": "string",
                "description": "Name of the agent to call.",
            },
            "query": {
                "type": "string",
                "description": "The question or task to send to the agent.",
            },
        }

    async def execute(self, agent_name: str, query: str, **_: Any) -> str:
        try:
            return await registry.call(agent_name, query)
        except KeyError:
            available = ", ".join(registry.agent_names)
            return f"Agent '{agent_name}' not found. Available: {available}"
