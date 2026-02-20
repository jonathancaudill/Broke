from __future__ import annotations

from broke.agents.base import BaseAgent
from broke.tools.call_agent import CallAgentTool
from broke.tools.rag_query import RAGQueryTool


class SkillsAgent(BaseAgent):
    name = "skills"
    description = (
        "Specialist in Jonathan's technical abilities — programming languages, "
        "frameworks, tools, and areas of expertise."
    )
    system_prompt = (
        "You are the Skills Specialist for Jonathan Caudill's portfolio agent system.\n\n"
        "Your job is to answer questions about Jonathan's technical skills, "
        "programming languages, frameworks, tools, and areas of expertise. "
        "Always use the rag_query tool to look up accurate information before "
        "answering — never guess or fabricate skills he doesn't have.\n\n"
        "If a question touches on how skills were applied in real projects or work "
        "experience, you may call the 'experience' or 'projects' agent for context.\n\n"
        "Be specific and concrete. If asked about proficiency level, ground it in "
        "what Jonathan has actually built."
    )

    def __init__(self) -> None:
        super().__init__()
        self.register_tool(RAGQueryTool())
        self.register_tool(CallAgentTool())
