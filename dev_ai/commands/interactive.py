"""Interactive command: continuous REPL chat with the AI assistant."""

from pathlib import Path

from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from dev_ai import config
from dev_ai.client import ask_llm
from dev_ai.commands._common import console, looks_like_error, print_error
from dev_ai.display import print_markdown

EXIT_WORDS = frozenset({"exit", "quit", "q"})

MAX_HISTORY = 20

SESSION_FILE = Path("dev-ai_session.txt")


def _save_session(path: Path, history: list[dict[str, str]]) -> None:
    """Persist the conversation history to *path* for later resumption."""
    lines: list[str] = []
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    console.print(f"[dim]Session saved to {path}[/dim]")


def _load_session(path: Path) -> list[dict[str, str]]:
    """Read a previously saved session back into message history."""
    history: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        role, _, content = stripped.partition(": ")
        if role in ("user", "assistant"):
            history.append({"role": role, "content": content})
    return history


def _offer_to_load_session(path: Path) -> list[dict[str, str]]:
    """If a session file exists, ask whether to resume it."""
    if not path.exists():
        return []
    try:
        from rich.prompt import Confirm

        if Confirm.ask(
            f"[yellow]Resume previous session from {path}?[/yellow]",
            default=True,
            console=console,
        ):
            try:
                history = _load_session(path)
                console.print(
                    f"[dim]Resumed {len(history) // 2} messages from history.[/dim]"
                )
                return history
            except (OSError, ValueError):
                pass
    except Exception:
        pass
    return []


def _handle_slash_command(
    text: str, history: list[dict[str, str]], session_model: str
) -> tuple[bool, str]:
    """Handle a slash command entered in the REPL.

    Args:
        text: The raw input line (starts with "/").
        history: The current session history (may be mutated by /clear).
        session_model: The model override for this session ("" = default).

    Returns:
        A tuple (handled, new_session_model). "handled" is False when the
        command is unknown; "new_session_model" carries any model change
        (or the unchanged value when not modified).
    """
    parts = text.split(maxsplit=1)
    name = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if name in ("/help", "/h", "/?"):
        _show_slash_help()
    elif name == "/clear":
        # reset screen and drop the whole conversation context
        history.clear()
        console.clear()
        console.print("[dim]Context cleared. Ask me anything.[/dim]")
    elif name == "/history":
        _show_history(history)
    elif name == "/model":
        session_model = _handle_model_command(arg, session_model)
    else:
        console.print(
            f"[bold yellow]Unknown command:[/bold yellow] {name}\n"
            "Type [bold]/help[/bold] to see available commands."
        )
        return False, session_model

    return True, session_model


def _show_slash_help() -> None:
    """Print the slash command reference in a Rich table."""
    table = Table(
        title="Slash commands", show_header=True, header_style="bold cyan"
    )
    table.add_column("Command", style="cyan")
    table.add_column("Description")

    table.add_row("/help", "Show this help message")
    table.add_row("/clear", "Clear the screen and reset conversation context")
    table.add_row("/history", "Show the message count and recent context")
    table.add_row("/model", "Show the current model or switch it for this session")
    table.add_row("/model <name>", "Switch to <name> (e.g. gpt-4o)")
    table.add_row("exit, quit, q", "Exit the REPL (also Ctrl+C / Ctrl+D)")

    console.print(table)


def _show_history(history: list[dict[str, str]]) -> None:
    """Print the conversation history summary."""
    count = len(history)
    if count == 0:
        console.print("[dim]No messages in this session yet.[/dim]")
        return

    console.print(
        f"[bold]{count} message(s)[/bold] in the current context "
        f"({count // 2} exchanges)."
    )
    if count <= 10:
        shown = history
    else:
        shown = history[-10:]
        console.print("[dim]Showing the last 10 messages:[/dim]")

    table = Table(show_header=True, header_style="bold cyan", box=None)
    table.add_column("Role", style="cyan")
    table.add_column("Content")

    for msg in shown:
        role = msg.get("role", "?")
        content = msg.get("content", "")
        if len(content) > 60:
            content = content[:57] + "..."
        table.add_row(role, content)

    console.print(table)


def _handle_model_command(arg: str, current: str) -> str:
    """Show or switch the LLM model for this session.

    Args:
        arg: The text after "/model" (empty to just display).
        current: The current session model override ("" = use config default).

    Returns:
        The new session model override.
    """
    active = current.strip() or config.get_model()
    if not arg:
        console.print(f"[bold]Current model:[/bold] {active}")
        if current:
            console.print(
                f"[dim]Session override: {current} "
                f"(default: {config.DEFAULT_MODEL})[/dim]"
            )
        return current

    if Confirm.ask(
        f"Switch model from [cyan]{active}[/cyan] to [cyan]{arg}[/cyan]?",
        default=True,
        console=console,
    ):
        console.print(f"[green]Model switched to {arg} for this session.[/green]")
        return arg
    console.print("[dim]Model unchanged.[/dim]")
    return current


def _read_line() -> str:
    """Read one line of the REPL input (patched in tests)."""
    return Prompt.ask("[bold cyan]dev-ai >[/bold cyan]")


def start_interactive_mode() -> int:
    """Chat with the AI assistant until the user exits.

    Every answer becomes part of the session history, so follow-up
    questions keep the conversation context. The loop ends on the
    exit, quit or q commands, on Ctrl+C (KeyboardInterrupt) or on
    Ctrl+D (EOFError).

    Returns:
        The CLI exit code: 0 on a clean exit.
    """
    console.print(
        Panel(
            "[bold]dev-ai interactive mode[/bold]\n"
            "Ask anything; the session keeps the conversation history.\n"
            "Type [bold]exit[/bold], [bold]quit[/bold] or [bold]q[/bold] "
            "to leave, or press Ctrl+C / Ctrl+D.",
            title="dev-ai",
            border_style="cyan",
        )
    )
    # Load existing session if present
    history: list[dict[str, str]] = _offer_to_load_session(SESSION_FILE)
    session_model: str = ""

    while True:
        try:
            line = _read_line()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Bye![/dim]")
            _save_session(SESSION_FILE, history)
            return 0

        text = (line or "").strip()
        if not text:
            continue
        if text.lower() in EXIT_WORDS:
            console.print("[dim]Bye![/dim]")
            _save_session(SESSION_FILE, history)
            return 0

        # Slash commands are handled locally, never sent to the LLM.
        if text.startswith("/"):
            _, session_model = _handle_slash_command(text, history, session_model)
            continue

        with console.status("[bold cyan]Thinking...[/bold cyan]"):
            message = ask_llm(text, model=session_model, history=history)

        if looks_like_error(message):
            print_error(message)
            continue

        answer = message.strip()
        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": answer})
        if len(history) > MAX_HISTORY:
            del history[: len(history) - MAX_HISTORY]

        print_markdown(answer)
