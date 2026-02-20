from __future__ import annotations

from typing import Any

from broke.tools.base import BaseTool


class CheckAvailabilityTool(BaseTool):
    """Check Jonathan's calendar for open meeting slots.

    STUB — returns placeholder data. Wire up a real calendar API
    (Google Calendar, Cal.com, etc.) to make this functional.
    """

    @property
    def name(self) -> str:
        return "check_availability"

    @property
    def description(self) -> str:
        return (
            "Check Jonathan's calendar availability for a given date range. "
            "Returns a list of open time slots."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "start_date": {
                "type": "string",
                "description": "Start of the date range (ISO 8601, e.g. 2026-02-20).",
            },
            "end_date": {
                "type": "string",
                "description": "End of the date range (ISO 8601, e.g. 2026-02-27).",
            },
        }

    async def execute(self, start_date: str, end_date: str, **_: Any) -> str:
        # TODO: replace with real calendar API integration
        return (
            f"[STUB] Available slots between {start_date} and {end_date}:\n"
            "  - Mon 10:00–11:30 AM CST\n"
            "  - Tue 2:00–4:00 PM CST\n"
            "  - Thu 9:00–10:00 AM CST\n"
            "  - Fri 1:00–3:00 PM CST\n\n"
            "Note: this is placeholder data. Calendar integration is not yet wired up."
        )


class BookMeetingTool(BaseTool):
    """Book a meeting with Jonathan.

    STUB — logs the request. Wire up a real calendar API to make this functional.
    """

    @property
    def name(self) -> str:
        return "book_meeting"

    @property
    def description(self) -> str:
        return (
            "Book a meeting with Jonathan at a specific time. "
            "Requires a time slot, the requester's name, and their email."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "datetime": {
                "type": "string",
                "description": "Requested meeting time (ISO 8601, e.g. 2026-02-24T14:00:00).",
            },
            "name": {
                "type": "string",
                "description": "Name of the person requesting the meeting.",
            },
            "email": {
                "type": "string",
                "description": "Contact email for the meeting requester.",
            },
            "topic": {
                "type": "string",
                "description": "Brief topic or agenda for the meeting.",
            },
        }

    async def execute(
        self, datetime: str, name: str, email: str, topic: str = "", **_: Any,
    ) -> str:
        # TODO: replace with real calendar booking + notification
        return (
            f"[STUB] Meeting request logged:\n"
            f"  Time:  {datetime}\n"
            f"  With:  {name} ({email})\n"
            f"  Topic: {topic or 'not specified'}\n\n"
            "Note: this is a scaffold. Calendar booking is not yet wired up — "
            "Jonathan has not actually been notified."
        )
