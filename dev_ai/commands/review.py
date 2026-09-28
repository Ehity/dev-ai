"""Code review command."""

from pathlib import Path

from rich.console import Console
from rich.markup import escape

from dev_ai.client import ask_llm
from dev_ai.prompts import CODE_REVIEW_SYSTEM_PROMPT

console = Console()

ERROR_PREFIXES = ("[config error]", "[network error]", "[api error]")


def _looks_like_error(message: str) -> bool:
    """Return True when ask_llm reported a configuration or API error."""
    return message.startswith(ERROR_PREFIXES)


def review_code(file_path: str) -> str:
    """Review a single source file and return the model reply.

    Returns an empty string when the file is missing, unreadable,
    or when the request failed.
    """
    path = Path(file_path)
    if not path.exists():
        console.print(
            "[bold red]Error:[/bold red] file not found: " + escape(str(path))
        )
        return ""
    if not path.is_file():
        console.print(
            "[bold red]Error:[/bold red] not a file: " + escape(str(path))
        )
        return ""

    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        console.print(
            "[bold red]Error:[/bold red] cannot read the file: " + escape(str(exc))
        )
        return ""

    prompt = CODE_REVIEW_SYSTEM_PROMPT + "\n\n" + source

    with console.status("[bold cyan]Reviewing the code...[/bold cyan]"):
        message = ask_llm(prompt)

    if _looks_like_error(message):
        console.print("[bold red]" + escape(message) + "[/bold red]")
        return ""

    console.print(message)
    return message.strip()
