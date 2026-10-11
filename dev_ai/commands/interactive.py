"""Interactive command: continuous REPL chat with the AI assistant."""

from rich.panel import Panel
from rich.prompt import Prompt

from dev_ai.client import ask_llm
from dev_ai.commands._common import console, looks_like_error, print_error
from dev_ai.display import print_markdown

EXIT_WORDS = frozenset({"exit", "quit", "q"})

MAX_HISTORY = 20


def _read_line() -> str:
    """Read one line of the REPL input (patched in tests)."""
    return Prompt.ask("\n[bold cyan]dev-ai >[/bold cyan]")


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

    history: list[dict[str, str]] = []
    while True:
        try:
            line = _read_line()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Bye![/dim]")
            return 0

        text = (line or "").strip()
        if not text:
            continue
        if text.lower() in EXIT_WORDS:
            console.print("[dim]Bye![/dim]")
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
