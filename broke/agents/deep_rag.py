from __future__ import annotations

from broke.agents.base import BaseAgent
from broke.tools.rag_query import RAGQueryTool


class DeepRAGAgent(BaseAgent):
    name = "deep_rag"
    description = (
        "Performs thorough, multi-pass retrieval for complex questions "
        "that need cross-referencing or exhaustive coverage."
    )
    system_prompt = (
        "You are the Deep RAG Agent for Jonathan Caudill's portfolio system.\n\n"
        "Your job is to perform thorough, multi-pass retrieval for questions that "
        "need more depth than a single query can provide. You have the same "
        "rag_query tool as the orchestrator, but your mandate is to be exhaustive.\n\n"
        "Strategy:\n"
        "1. Start with a broad query across all collections.\n"
        "2. Based on initial results, formulate more specific follow-up queries "
        "   targeting individual collections (resume, projects, skills, background).\n"
        "3. Cross-reference findings — if a skill is mentioned, look for projects "
        "   that demonstrate it. If a role is mentioned, look for specifics.\n"
        "4. Don't stop after one or two queries. Iterate until you have a "
        "   comprehensive picture.\n\n"
        "Return a well-structured summary of everything you found, organised by "
        "theme rather than by query. Flag any gaps or contradictions."
    )
    max_iterations = 15

    def __init__(self) -> None:
        super().__init__()
        self.register_tool(RAGQueryTool())
