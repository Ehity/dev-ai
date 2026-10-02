"""Code review command."""

from pathlib import Path
from typing import Optional

from rich.markup import escape

from dev_ai.client import ask_llm
from dev_ai.commands._common import (
    console,
    looks_like_error,
    print_error,
    print_warning,
    require_file,
)
from dev_ai.commands.commit import get_staged_diff, get_unstaged_diff
from dev_ai.display import print_markdown
from dev_ai.prompts import CODE_REVIEW_SYSTEM_PROMPT

MAX_FILE_SIZE = 200000


def _read_file(path: Path) -> Optional[str]:
    """Return the source text, or None when the file cannot be reviewed.

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
    if not require_file(path, kind="source"):
        return None

    source = _read_file(path)
    if source is None:
        return None
    if not source.strip():
        print_warning("the file is empty: " + escape(str(path)))
        return None

    return "Review the following file: " + str(path) + "\n\n" + source


def _diff_request() -> Optional[str]:
    """Build a review request for the uncommitted changes, or None."""
    diff = get_staged_diff(quiet=True)
    if not diff.strip():
        diff = get_unstaged_diff(quiet=True)
    if not diff.strip():
        print_warning("nothing to review: no staged or unstaged changes found.")
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

    if looks_like_error(message):
        print_error(message)
        return ""

    review = message.strip()
    print_markdown(review)
    return review
