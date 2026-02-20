from __future__ import annotations

from typing import Any

from broke.config import get_settings


class ConversationMemory:
    """Sliding-window conversation history.

    Stores the full history but only exposes the most recent *window_size*
    turns when building context for agents.
    """

    def __init__(self, window_size: int | None = None) -> None:
        self._history: list[dict[str, Any]] = []
        self._window = window_size or get_settings().memory_window

    def add_user(self, content: str) -> None:
        self._history.append({"role": "user", "content": content})

    def add_assistant(self, content: str) -> None:
        self._history.append({"role": "assistant", "content": content})

    def get_window(self) -> list[dict[str, Any]]:
        """Return the most recent messages within the window."""
        return self._history[-self._window :]

    def get_context(self) -> dict[str, Any]:
        """Return a context dict suitable for passing to agents."""
        return {"history": self.get_window()}

    def clear(self) -> None:
        self._history.clear()

    @property
    def full_history(self) -> list[dict[str, Any]]:
        return list(self._history)

    def __len__(self) -> int:
        return len(self._history)
