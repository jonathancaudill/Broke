from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from broke.agents.registry import registry

log = logging.getLogger(__name__)


@dataclass(eq=False)
class AgentTask:
    """A dispatched specialist task with its asyncio future."""

    agent_name: str
    query: str
    context: dict[str, Any] | None = None
    _task: asyncio.Task[str] | None = field(default=None, repr=False)

    @property
    def task(self) -> asyncio.Task[str]:
        assert self._task is not None, "Task not yet dispatched"
        return self._task


class EventBus:
    """Async dispatch / collection layer for the orchestrator.

    Fires off specialist agents as concurrent asyncio tasks and provides
    an interface to collect results as they finish.
    """

    async def dispatch(
        self, agent_name: str, query: str, context: dict[str, Any] | None = None
    ) -> AgentTask:
        log.debug("[bus] dispatching '%s' with query: %s", agent_name, query[:200])
        at = AgentTask(agent_name=agent_name, query=query, context=context)
        at._task = asyncio.create_task(
            registry.call(agent_name, query, context),
            name=f"agent:{agent_name}",
        )
        return at

    async def dispatch_all(
        self, tasks: list[dict[str, Any]]
    ) -> set[AgentTask]:
        """Dispatch multiple agent tasks concurrently.

        Each item in *tasks* is ``{"agent": str, "query": str, "context": dict | None}``.
        """
        agent_tasks: set[AgentTask] = set()
        for t in tasks:
            at = await self.dispatch(
                t["agent"], t["query"], t.get("context")
            )
            agent_tasks.add(at)
        return agent_tasks

    @staticmethod
    async def wait_next(
        pending: set[AgentTask], timeout: float | None = None
    ) -> tuple[list[tuple[str, str]], set[AgentTask]]:
        """Wait for at least one task to complete.

        Returns ``(completed, still_pending)`` where *completed* is a list
        of ``(agent_name, result_string)`` tuples.
        """
        asyncio_tasks = {at.task: at for at in pending}
        done, _still = await asyncio.wait(
            asyncio_tasks.keys(),
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED,
        )

        completed: list[tuple[str, str]] = []
        remaining = set(pending)
        for finished_task in done:
            at = asyncio_tasks[finished_task]
            remaining.discard(at)
            try:
                result = finished_task.result()
                log.debug("[bus] '%s' finished (%d chars)", at.agent_name, len(result))
            except Exception as exc:
                result = f"Agent '{at.agent_name}' failed: {exc}"
                log.exception("[bus] '%s' raised an exception", at.agent_name)
            completed.append((at.agent_name, result))

        if remaining:
            log.debug("[bus] still pending: %s", [at.agent_name for at in remaining])
        return completed, remaining
