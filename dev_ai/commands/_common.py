"""Shared helpers for dev-ai commands."""

import subprocess
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

ERROR_PREFIXES = ("[config error]", "[network error]", "[api error]")

PYTHON_SUFFIX = ".py"


def looks_like_error(message: str) -> bool:
    """Return True when ask_llm reported a configuration or API error."""
    return message.startswith(ERROR_PREFIXES)


def print_error(message: str) -> None:
    """Print an error reported by the LLM client."""
    console.print("[bold red]" + escape(message) + "[/bold red]")


def read_source(path: Path) -> Optional[str]:
    """Read the file as UTF-8 text, or None when it is not readable."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        console.print(
            "[bold red]Error:[/bold red] cannot read the file: " + escape(str(exc))
        )
        return None


def print_warning(message: str) -> None:
    """Print a warning line."""
    console.print("[bold yellow]Warning:[/bold yellow] " + message)


def require_file(path: Path, kind: str = "file") -> bool:
    """Return True when the path points to an existing file.

    Prints an informative error when the file is missing or when the
    path points to a directory.
    """
    if not path.exists():
        console.print(
            "[bold red]Error:[/bold red] file not found: "
            + escape(str(path))
            + "; check the path and try again."
        )
        return False
    if not path.is_file():
        console.print(
            "[bold red]Error:[/bold red] not a file: "
            + escape(str(path))
            + f"; pass a path to a {kind} file."
        )
        return False
    return True


def is_git_repository() -> bool:
    """Return True when the current directory is inside a git work tree."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        console.print(
            "[bold yellow]Warning:[/bold yellow] git is not installed "
            "or is not available in PATH."
        )
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def run_git_diff(args: List[str]) -> Optional[str]:
    """Run git diff with the given extra arguments.

    Returns the diff text, or None when the command cannot be run.
    A warning is printed in that case.
    """
    try:
        result = subprocess.run(
            ["git", "diff"] + args,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        console.print(
            "[bold yellow]Warning:[/bold yellow] git is not installed "
            "or is not available in PATH."
        )
        return None

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        console.print(
            "[bold yellow]Warning:[/bold yellow] git diff failed: " + escape(detail)
        )
        return None

    return result.stdout


def extract_code_block(text: str) -> str:
    """Return the code from the first Markdown fence, or the whole text."""
    marker = "```"
    if marker not in text:
        return text

    parts = text.split(marker)
    if len(parts) < 3:
        return text

    block = parts[1]
    lines = block.splitlines()
    if lines and lines[0].strip().lower() in ("python", "py", "python3"):
        lines = lines[1:]
    return chr(10).join(lines).strip()


def print_code(path: Path, code: str) -> None:
    """Print Python source with syntax highlighting."""
    console.print(
        Panel(
            Syntax(code, "python", theme="monokai", line_numbers=True),
            title=str(path),
            border_style="cyan",
        )
    )
