"""Code review command."""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.markup import escape

from dev_ai.client import ask_llm
from dev_ai.commands.commit import get_staged_diff, get_unstaged_diff
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


def _file_request(path: Path) -> Optional[str]:
    """Build a review request for a single file, or None on failure."""
    if not path.exists():
        console.print(
            "[bold red]Error:[/bold red] file not found: " + escape(str(path))
        )
        return None
    if not path.is_file():
        console.print(
            "[bold red]Error:[/bold red] not a file: " + escape(str(path))
        )
        return None

    source = _read_source(path)
    if source is None:
        return None
    if not source.strip():
        console.print(
            "[bold yellow]Warning:[/bold yellow] the file is empty: "
            + escape(str(path))
        )
        return None

    return "Review the following file: " + str(path) + "\n\n" + source


def _diff_request() -> Optional[str]:
    """Build a review request for the uncommitted changes, or None."""
    diff = get_staged_diff(quiet=True)
    if not diff.strip():
        diff = get_unstaged_diff(quiet=True)
    if not diff.strip():
        console.print(
            "[bold yellow]Warning:[/bold yellow] nothing to review: no staged "
            "or unstaged changes found."
        )
        return None
    return "Review the following git diff of uncommitted changes:\n\n" + diff


def review_code(file_path: Optional[str] = None) -> str:
    """Review a file or the uncommitted changes and print the result.

    Args:
        file_path: Path to the file to review. When omitted, the current
            git diff (staged changes, falling back to unstaged ones)
            is reviewed instead.

    Returns the review text, or an empty string when there is nothing
    to review or when the request failed.
    """
    if file_path is None:
        request = _diff_request()
    else:
        request = _file_request(Path(file_path))
    if request is None:
        return ""

    prompt = CODE_REVIEW_SYSTEM_PROMPT + "\n\n" + request

    with console.status("[bold cyan]Reviewing the code...[/bold cyan]"):
        message = ask_llm(prompt)

    if _looks_like_error(message):
        console.print("[bold red]" + escape(message) + "[/bold red]")
        return ""

    review = message.strip()
    print_markdown(review)
    return review
