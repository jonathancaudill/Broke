from __future__ import annotations

from broke.agents.base import BaseAgent
from broke.tools.scheduling import BookMeetingTool, CheckAvailabilityTool


class SchedulingAgent(BaseAgent):
    name = "scheduling"
    description = (
        "Handles meeting scheduling — checks Jonathan's availability "
        "and books meetings on his calendar."
    )
    system_prompt = (
        "You are the Scheduling Agent for Jonathan Caudill's portfolio system.\n\n"
        "Your job is to help people set up meetings with Jonathan. Use the "
        "check_availability tool to find open time slots, then use book_meeting "
        "to confirm a slot once the requester picks one.\n\n"
        "Be helpful and efficient. If the requester hasn't specified a date range, "
        "ask for one. If they haven't given their name and email, ask for those "
        "before booking.\n\n"
        "Keep responses short and action-oriented."
    )

    def __init__(self) -> None:
        super().__init__()
        self.register_tool(CheckAvailabilityTool())
        self.register_tool(BookMeetingTool())
