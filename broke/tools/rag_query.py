from __future__ import annotations

import json
from typing import Any

from broke.knowledge.store import query
from broke.tools.base import BaseTool


class RAGQueryTool(BaseTool):
    """Search the knowledge base for relevant information."""

    @property
    def name(self) -> str:
        return "rag_query"

    @property
    def description(self) -> str:
        return (
            "Search the knowledge base for information about Jonathan — "
            "his resume, projects, skills, and background. "
            "Specify a collection to narrow results: 'resume', 'projects', "
            "'skills', or 'background'. Use 'all' to search everything."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "The search query describing what information you need.",
            },
            "collection": {
                "type": "string",
                "description": (
                    "Which knowledge collection to search. "
                    "One of: resume, projects, skills, background, all."
                ),
                "enum": ["resume", "projects", "skills", "background", "all"],
            },
        }

    async def execute(self, query: str, collection: str = "all", **_: Any) -> str:
        collections = (
            ["resume", "projects", "skills", "background"]
            if collection == "all"
            else [collection]
        )

        all_results: list[dict[str, Any]] = []
        for coll in collections:
            results = query_collection(coll, query)
            all_results.extend(results)

        if not all_results:
            return "No relevant information found in the knowledge base."

        all_results.sort(key=lambda r: r.get("distance", float("inf")))
        top = all_results[:5]

        formatted = []
        for r in top:
            source = r.get("metadata", {}).get("source", "unknown")
            section = r.get("metadata", {}).get("section", "")
            formatted.append(f"[{source} / {section}]\n{r['text']}")

        return "\n---\n".join(formatted)


def query_collection(collection_name: str, query_text: str) -> list[dict[str, Any]]:
    """Thin wrapper to avoid name collision with the parameter."""
    return query(collection_name, query_text)
