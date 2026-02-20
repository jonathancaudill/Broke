from __future__ import annotations

import abc
from typing import Any


class BaseTool(abc.ABC):
    """Every tool exposes a name, description, JSON-schema for parameters,
    and an async execute method."""

    @property
    @abc.abstractmethod
    def name(self) -> str: ...

    @property
    @abc.abstractmethod
    def description(self) -> str: ...

    @property
    @abc.abstractmethod
    def parameters_schema(self) -> dict[str, Any]:
        """JSON Schema describing the tool's parameters (the 'properties' object)."""
        ...

    @abc.abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """Run the tool and return a string result."""
        ...

    def to_openai_tool(self) -> dict[str, Any]:
        """Serialise to the OpenAI function-calling tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters_schema,
                    "required": list(self.parameters_schema.keys()),
                },
            },
        }
