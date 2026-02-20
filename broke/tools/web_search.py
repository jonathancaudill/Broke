from __future__ import annotations

from typing import Any

from broke.tools.base import BaseTool


class WebSearchTool(BaseTool):
    """Search the web for current information.

    STUB — returns placeholder results. Wire up a real search API
    (Tavily, SerpAPI, Brave Search, etc.) to make this functional.
    """

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search the web for current or external information. "
            "Use this when the question requires up-to-date data that "
            "isn't in Jonathan's knowledge base."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "The search query to look up.",
            },
        }

    async def execute(self, query: str, **_: Any) -> str:
        # TODO: replace with real search API (Tavily, SerpAPI, etc.)
        return (
            f"[STUB] Web search for: {query!r}\n\n"
            "No real results — web search integration is not yet wired up.\n"
            "When implemented, this tool will return summarised search results "
            "from a search API."
        )
