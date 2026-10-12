"""Interactive command: continuous REPL chat with the AI assistant."""

from pathlib import Path

from rich.panel import Panel
from rich.prompt import Prompt

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

        with console.status("[bold cyan]Thinking...[/bold cyan]"):
            message = ask_llm(text, history=history)

        if looks_like_error(message):
            print_error(message)
            continue

        answer = message.strip()
        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": answer})
        if len(history) > MAX_HISTORY:
            del history[: len(history) - MAX_HISTORY]

        print_markdown(answer)
