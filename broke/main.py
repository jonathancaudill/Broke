"""Broke — terminal REPL entry point."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from broke import prompts
from broke.agents.deep_rag import DeepRAGAgent
from broke.agents.orchestrator import Orchestrator
from broke.agents.registry import registry
from broke.agents.researcher import ResearcherAgent
from broke.agents.scheduling import SchedulingAgent
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
    specialists = [
        SchedulingAgent(),
        ResearcherAgent(),
        DeepRAGAgent(),
    ]
    for agent in specialists:
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
        "[dim]Commands:\n"
        "  /ask <agent> <query>  Run a single agent in isolation\n"
        "  /chat <query>         Talk to the LLM directly (no tools/agents)\n"
        "  /reload               Hot-reload all prompts from disk\n"
        "  /prompt [agent]       Show system prompt (all or one)\n"
        "  /thinking [level]     Set reasoning effort: minimal / low / medium / high\n"
        "  /agents               List available agents\n"
        "  /debug                Toggle debug mode\n"
        "  /clear                Reset conversation\n"
        "  /quit                 Exit[/dim]\n"
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
            "thinking", "thinking_end", "agent_thinking", "agent_thinking_end", "token",
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
        elif msg_type == "ack_break":
            console.print()

        elif msg_type == "status":
            console.print(f"  [dim italic]{msg['content']}[/dim italic]")

        elif msg_type == "token":
            console.file.write(msg["content"])
            console.file.flush()

        elif msg_type == "final":
            final_content = msg["content"]
            console.print()
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

async def _handle_ask(agent_name: str, query: str, debug: bool) -> None:
    """Run a single agent in isolation and print its result."""
    try:
        agent = registry.get(agent_name)
    except KeyError:
        console.print(f"[red]Unknown agent: {agent_name}[/red]")
        console.print(f"[dim]Available: {', '.join(registry.agent_names)}[/dim]")
        return

    console.print(f"\n[bold cyan]─── {agent_name} ───[/bold cyan]")
    t0 = time.perf_counter()
    try:
        result = await agent.run(query)
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        if debug:
            console.print_exception()
        return
    elapsed = time.perf_counter() - t0

    console.print()
    console.print(Markdown(result))
    console.print(f"\n[dim]({elapsed:.1f}s)[/dim]")


async def _handle_chat(query: str, debug: bool) -> None:
    """Send a query straight to the LLM with only the personality prompt — no routing, no tools.

    Streams tokens to the terminal as they arrive.
    """
    from broke.llm.provider import stream_completion

    console.print("\n[bold cyan]─── direct chat ───[/bold cyan]\n")
    t0 = time.perf_counter()
    collected = ""
    try:
        async for token in stream_completion(
            [
                {"role": "system", "content": prompts.personality()},
                {"role": "user", "content": query},
            ],
            temperature=0.7,
        ):
            console.file.write(token)
            console.file.flush()
            collected += token
    except Exception as exc:
        console.print(f"\n[red]Error: {exc}[/red]")
        if debug:
            console.print_exception()
        return
    elapsed = time.perf_counter() - t0

    if not collected:
        console.print("[dim](empty response)[/dim]")
    console.print(f"\n\n[dim]({elapsed:.1f}s)[/dim]")


def _handle_prompt_cmd(arg: str) -> None:
    """Show the effective system prompt for one or all agents."""
    if arg:
        try:
            agent = registry.get(arg)
        except KeyError:
            console.print(f"[red]Unknown agent: {arg}[/red]")
            return
        console.print(f"\n[bold cyan]{arg}[/bold cyan]")
        prompt_text = (
            agent._build_system_prompt()
            if arg == "orchestrator"
            else agent.get_system_prompt()
        )
        console.print(Panel(prompt_text, border_style="dim"))
    else:
        for info in registry.list_agents():
            name = info["name"]
            agent = registry.get(name)
            console.print(f"\n[bold cyan]{name}[/bold cyan]")
            prompt_text = (
                agent._build_system_prompt()
                if name == "orchestrator"
                else agent.get_system_prompt()
            )
            if len(prompt_text) > 500:
                prompt_text = prompt_text[:500] + "\n..."
            console.print(Panel(prompt_text, border_style="dim"))


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

        low = user_input.lower()

        if low in ("/quit", "/exit", "/q"):
            console.print("[dim]Later.[/dim]")
            break

        if low == "/clear":
            memory.clear()
            console.print("[dim]Conversation cleared.[/dim]\n")
            continue

        if low == "/debug":
            debug = not debug
            _setup_logging(debug)
            state = "ON" if debug else "OFF"
            console.print(f"[dim]Debug mode: {state}[/dim]\n")
            continue

        if low == "/reload":
            loaded = prompts.reload()
            console.print("[dim]Reloaded prompts:[/dim]")
            for f in loaded:
                console.print(f"  [dim]✓ {f}[/dim]")
            console.print()
            continue

        if low.startswith("/thinking"):
            from broke.llm.provider import (
                VALID_REASONING_EFFORTS,
                get_reasoning_effort,
                set_reasoning_effort,
            )
            arg = user_input[9:].strip().lower()
            if not arg:
                current = get_reasoning_effort() or "default (model decides)"
                console.print(f"[dim]Reasoning effort: {current}[/dim]")
                console.print(f"[dim]Options: {', '.join(VALID_REASONING_EFFORTS)}[/dim]\n")
                continue
            try:
                set_reasoning_effort(arg)
                console.print(f"[dim]Reasoning effort → {arg}[/dim]\n")
            except ValueError:
                console.print(f"[red]Invalid. Choose from: {', '.join(VALID_REASONING_EFFORTS)}[/red]\n")
            continue

        if low == "/agents":
            for info in registry.list_agents():
                console.print(
                    f"  [cyan]{info['name']}[/cyan] — {info['description']}"
                )
            console.print()
            continue

        if low.startswith("/prompt"):
            arg = user_input[7:].strip()
            _handle_prompt_cmd(arg)
            console.print()
            continue

        if low.startswith("/chat "):
            query = user_input[6:].strip()
            if not query:
                console.print("[dim]Usage: /chat <query>[/dim]")
                continue
            try:
                await _handle_chat(query, debug)
            except Exception as exc:
                console.print(f"\n[red]Error: {exc}[/red]")
                if debug:
                    console.print_exception()
            console.print()
            continue

        if low.startswith("/ask "):
            parts = user_input[5:].strip().split(None, 1)
            if len(parts) < 2:
                console.print("[dim]Usage: /ask <agent> <query>[/dim]")
                continue
            agent_name, query = parts
            try:
                await _handle_ask(agent_name.lower(), query, debug)
            except Exception as exc:
                console.print(f"\n[red]Error: {exc}[/red]")
                if debug:
                    console.print_exception()
            console.print()
            continue

        if low.startswith("/"):
            console.print("[dim]Unknown command. Type a question or see commands above.[/dim]\n")
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
