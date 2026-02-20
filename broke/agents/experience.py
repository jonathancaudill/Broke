from __future__ import annotations

from broke.agents.base import BaseAgent
from broke.tools.call_agent import CallAgentTool
from broke.tools.rag_query import RAGQueryTool


class ExperienceAgent(BaseAgent):
    name = "experience"
    description = (
        "Specialist in Jonathan's work history, roles, achievements, "
        "and professional background."
    )
    system_prompt = (
        "You are the Experience Specialist for Jonathan Caudill's portfolio agent system.\n\n"
        "Your job is to answer questions about Jonathan's work history, job roles, "
        "professional achievements, and career trajectory. Always use the rag_query "
        "tool to look up accurate information from the resume and background collections.\n\n"
        "If a question also involves specific projects or technical skills used in a role, "
        "you may call the 'projects' or 'skills' agent for additional detail.\n\n"
        "Be honest and accurate. Don't embellish — Jonathan's real experience speaks for itself."
    )

    def __init__(self) -> None:
        super().__init__()
        self.register_tool(RAGQueryTool())
        self.register_tool(CallAgentTool())
