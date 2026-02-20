from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from broke.agents.base import BaseAgent


class AgentRegistry:
    """Global registry for agent discovery and peer-to-peer calls."""

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> BaseAgent:
        try:
            return self._agents[name]
        except KeyError:
            raise KeyError(f"No agent registered with name '{name}'") from None

    async def call(
        self, name: str, query: str, context: dict[str, Any] | None = None
    ) -> str:
        agent = self.get(name)
        return await agent.run(query, context)

    def list_agents(self) -> list[dict[str, str]]:
        return [
            {"name": a.name, "description": a.description}
            for a in self._agents.values()
        ]

    @property
    def agent_names(self) -> list[str]:
        return list(self._agents.keys())


# Singleton — shared across the application
registry = AgentRegistry()
