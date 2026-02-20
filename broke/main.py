"""Broke — terminal REPL entry point."""

from __future__ import annotations

import asyncio
import json
import logging
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from broke.agents.culture import CultureFitAgent
from broke.agents.experience import ExperienceAgent
from broke.agents.orchestrator import Orchestrator
from broke.agents.projects import ProjectsAgent
from broke.agents.registry import registry
from broke.agents.skills import SkillsAgent
from broke.config import get_settings
from broke.knowledge.ingest import ingest_all
from broke.memory.conversation import ConversationMemory

console = Console()


def _setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(name)s | %(levelname)s | %(message)s",
    )


def _register_agents() -> Orchestrator:
    """Instantiate and register all agents. Returns the orchestrator."""
    skills = SkillsAgent()
    experience = ExperienceAgent()
    projects = ProjectsAgent()
    culture = CultureFitAgent()

    for agent in [skills, experience, projects, culture]:
        registry.register(agent)

    orchestrator = Orchestrator()
    registry.register(orchestrator)
    return orchestrator


def _print_banner() -> None:
    banner = Text.assemble(
        ("BROKE", "bold magenta"),
        (" — Jonathan Caudill's Portfolio Agent", "dim"),
    )
    console.print(Panel(banner, border_style="magenta", padding=(0, 2)))
    console.print(
        "[dim]Type a question, /debug to toggle debug mode, "
        "/clear to reset conversation, /quit to exit.[/dim]\n"
    )


# ------------------------------------------------------------------
# Stream renderer
# ------------------------------------------------------------------

async def _handle_message(
    orchestrator: Orchestrator,
    query: str,
    memory: ConversationMemory,
    debug: bool,
) -> None:
    """Iterate the orchestrator stream and render every event to the terminal."""
    context = memory.get_context()
    final_content = ""
    in_thinking = False
    thinking_source: str | None = None

    async for msg in orchestrator.run_stream(query, context, debug=debug):
        msg_type = msg["type"]

        # Close an open thinking block when a non-thinking event arrives
        if in_thinking and msg_type not in (
            "thinking", "thinking_end", "agent_thinking", "agent_thinking_end",
        ):
            console.print()
            in_thinking = False
            thinking_source = None

        # --- Orchestrator thinking (always visible) ---
        if msg_type == "thinking":
            phase = msg.get("phase", "")
            if not in_thinking or thinking_source != phase:
                if in_thinking:
                    console.print()
                label = phase or "thinking"
                console.print(Text(f"\n  💭 {label}", style="dim bold yellow"))
                thinking_source = phase
                in_thinking = True
            console.print(Text(msg["content"], style="dim italic yellow"), end="")

        elif msg_type == "thinking_end":
            if in_thinking:
                console.print()
                in_thinking = False
                thinking_source = None

        # --- Standard orchestrator events ---
        elif msg_type == "ack":
            console.print(f"\n[cyan]{msg['content']}[/cyan]")

        elif msg_type == "status":
            console.print(f"  [dim italic]{msg['content']}[/dim italic]")

        elif msg_type == "final":
            final_content = msg["content"]
            console.print()
            console.print(Markdown(final_content))
            if debug and "sources" in msg:
                sources = ", ".join(msg["sources"])
                console.print(f"\n  [dim]agents consulted: {sources}[/dim]")

        # --- Debug-only agent events ---
        elif debug and msg_type == "agent_input":
            agent = msg.get("agent", "?")
            console.print(
                Text(f"\n  ▶ [{agent}] query: {msg.get('query', '')}", style="dim yellow")
            )

        elif debug and msg_type == "agent_thinking":
            agent = msg.get("agent", "?")
            if not in_thinking or thinking_source != agent:
                if in_thinking:
                    console.print()
                console.print(Text(f"    💭 [{agent}] ", style="dim"), end="")
                thinking_source = agent
                in_thinking = True
            console.print(Text(msg["content"], style="dim italic"), end="")

        elif debug and msg_type == "agent_thinking_end":
            if in_thinking:
                console.print()
                in_thinking = False
                thinking_source = None

        elif debug and msg_type == "agent_tool_call":
            agent = msg.get("agent", "?")
            tool = msg.get("tool", "?")
            args_str = json.dumps(msg.get("args", {}), default=str)
            if len(args_str) > 200:
                args_str = args_str[:200] + "..."
            console.print(
                Text(f"    🔧 [{agent}] {tool}({args_str})", style="dim yellow")
            )

        elif debug and msg_type == "agent_tool_result":
            agent = msg.get("agent", "?")
            content = msg.get("content", "")
            if len(content) > 300:
                content = content[:300] + "..."
            console.print(Text(f"    ← [{agent}] {content}", style="dim"))

        elif debug and msg_type == "agent_output":
            agent = msg.get("agent", "?")
            content = msg.get("content", "")
            if len(content) > 500:
                content = content[:500] + "..."
            console.print(
                Text(f"\n  ◀ [{agent}] {content}", style="dim green")
            )

    if in_thinking:
        console.print()

    if final_content:
        memory.add_user(query)
        memory.add_assistant(final_content)


# ------------------------------------------------------------------
# REPL
# ------------------------------------------------------------------

async def _repl(orchestrator: Orchestrator, debug: bool) -> None:
    memory = ConversationMemory()
    _print_banner()

    while True:
        try:
            user_input = console.input("[bold green]you>[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Bye![/dim]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit", "/q"):
            console.print("[dim]Later.[/dim]")
            break

        if user_input.lower() == "/clear":
            memory.clear()
            console.print("[dim]Conversation cleared.[/dim]\n")
            continue

        if user_input.lower() == "/debug":
            debug = not debug
            _setup_logging(debug)
            state = "ON" if debug else "OFF"
            console.print(f"[dim]Debug mode: {state}[/dim]\n")
            continue

        try:
            await _handle_message(orchestrator, user_input, memory, debug)
        except Exception as exc:
            console.print(f"\n[red]Error: {exc}[/red]")
            if debug:
                console.print_exception()
        console.print()


def cli_entry() -> None:
    """Entry point for the `broke` console script."""
    settings = get_settings()
    _setup_logging(settings.debug)

    console.print("[dim]Initialising knowledge base...[/dim]")
    ingest_all()
    console.print("[dim]Knowledge base ready.[/dim]")

    orchestrator = _register_agents()
    console.print(f"[dim]Model: {settings.model}[/dim]")

    try:
        asyncio.run(_repl(orchestrator, debug=settings.debug))
    except KeyboardInterrupt:
        console.print("\n[dim]Bye![/dim]")
        sys.exit(0)


if __name__ == "__main__":
    cli_entry()
