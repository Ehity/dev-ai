"""Code review command."""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.markup import escape

from dev_ai.client import ask_llm
from dev_ai.display import print_markdown
from dev_ai.prompts import CODE_REVIEW_SYSTEM_PROMPT

console = Console()

ERROR_PREFIXES = ("[config error]", "[network error]", "[api error]")

MAX_FILE_SIZE = 200000


def _looks_like_error(message: str) -> bool:
    """Return True when ask_llm reported a configuration or API error."""
    return message.startswith(ERROR_PREFIXES)


def _read_source(path: Path) -> Optional[str]:
    """Return the text content of the file, or None when it cannot be read.

    Warns when the file is too large, looks binary, or is not valid UTF-8.
    """
    try:
        data = path.read_bytes()
    except OSError as exc:
        console.print(
            "[bold red]Error:[/bold red] cannot read the file: " + escape(str(exc))
        )
        return None

    size = len(data)
    if size > MAX_FILE_SIZE:
        limit = MAX_FILE_SIZE // 1024
        console.print(
            "[bold red]Error:[/bold red] file is too large to review: "
            f"{size} bytes, limit {limit} KB."
        )
        return None

    if b"\x00" in data:
        console.print(
            "[bold red]Error:[/bold red] looks like a binary file, not source code: "
            + escape(str(path))
        )
        return None

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        console.print(
            "[bold red]Error:[/bold red] cannot decode the file as UTF-8 text: "
            + escape(str(path))
        )
        return None


def review_code(file_path: str) -> str:
    """Review a source file and print the result as Markdown.

    Returns the review text, or an empty string when the file cannot
    be reviewed or when the request failed.
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

    source = _read_source(path)
    if source is None:
        return ""
    if not source.strip():
        console.print(
            "[bold yellow]Warning:[/bold yellow] the file is empty: "
            + escape(str(path))
        )
        return ""

    prompt = CODE_REVIEW_SYSTEM_PROMPT + "\n\n" + source

    with console.status("[bold cyan]Reviewing the code...[/bold cyan]"):
        message = ask_llm(prompt)

    if _looks_like_error(message):
        console.print("[bold red]" + escape(message) + "[/bold red]")
        return ""

    review = message.strip()
    print_markdown(review)
    return review
