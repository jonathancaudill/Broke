from __future__ import annotations

from broke.agents.base import BaseAgent
from broke.tools.web_search import WebSearchTool


class ResearcherAgent(BaseAgent):
    name = "researcher"
    description = (
        "Performs web research to answer questions that need current "
        "or external information beyond Jonathan's knowledge base."
    )
    system_prompt = (
        "You are the Researcher Agent for Jonathan Caudill's portfolio system.\n\n"
        "Your job is to search the web for information that isn't available in "
        "Jonathan's knowledge base — industry trends, company details, current "
        "events, technical documentation, etc.\n\n"
        "Use the web_search tool to find relevant results, then summarise the "
        "findings clearly and concisely. Cite your sources when possible.\n\n"
        "If the search returns nothing useful, say so honestly rather than "
        "making things up."
    )

    def __init__(self) -> None:
        super().__init__()
        self.register_tool(WebSearchTool())
