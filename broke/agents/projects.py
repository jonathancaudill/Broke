from __future__ import annotations

from broke.agents.base import BaseAgent
from broke.tools.call_agent import CallAgentTool
from broke.tools.rag_query import RAGQueryTool


class ProjectsAgent(BaseAgent):
    name = "projects"
    description = (
        "Specialist in Jonathan's project portfolio — what he's built, "
        "the tech behind it, and the problems each project solves."
    )
    system_prompt = (
        "You are the Projects Specialist for Jonathan Caudill's portfolio agent system.\n\n"
        "Your job is to answer questions about things Jonathan has built — personal "
        "projects, professional work, open source contributions, and side projects. "
        "Always use the rag_query tool to look up accurate project details.\n\n"
        "When describing projects, cover: what it does, the tech stack, interesting "
        "architectural decisions, and what problems it solves. If you need info about "
        "specific technologies used, call the 'skills' agent.\n\n"
        "Be enthusiastic but factual. Let the work speak for itself."
    )

    def __init__(self) -> None:
        super().__init__()
        self.register_tool(RAGQueryTool())
        self.register_tool(CallAgentTool())
