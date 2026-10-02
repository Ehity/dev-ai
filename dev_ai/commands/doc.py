"""Docstring generation command."""

from pathlib import Path

from rich.markup import escape
from rich.panel import Panel
from rich.syntax import Syntax

from dev_ai.client import ask_llm
from dev_ai.commands._common import (
    console,
    looks_like_error,
    print_error,
    print_warning,
    read_source,
    require_file,
)
from dev_ai.prompts import DOCSTRING_SYSTEM_PROMPT

BACKUP_SUFFIX = ".bak"


def _extract_code_block(text: str) -> str:
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


def _print_code(path: Path, code: str) -> None:
    """Print Python source with syntax highlighting."""
    console.print(
        Panel(
            Syntax(code, "python", theme="monokai", line_numbers=True),
            title=str(path),
            border_style="cyan",
        )
    )


def write_docs(path: Path, code: str) -> bool:
    """Write generated code back to the file, keeping a backup copy.

    Returns True when the file was written successfully.
    """
    backup = path.with_name(path.name + BACKUP_SUFFIX)
    try:
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        path.write_text(code + chr(10), encoding="utf-8")
    except OSError as exc:
        print_error("cannot write the file: " + str(exc))
        return False

    console.print(
        "[bold green]Updated[/bold green] "
        + escape(str(path))
        + " [dim](backup: "
        + escape(str(backup))
        + ")[/dim]"
    )
    return True


def generate_docs(file_path: str, write: bool = False) -> str:
    """Generate docstrings for the given Python source file.

    Args:
        file_path: Path to the Python file that needs docstrings.
        write: When True, save the result back to the file and keep a
            backup copy next to it.

    Returns the updated source, or an empty string when the file is
    missing or the request failed.
    """
    path = Path(file_path)
    if not require_file(path, kind="Python source"):
        return ""

    source = read_source(path)
    if source is None:
        return ""
    if not source.strip():
        print_warning("the file is empty: " + escape(str(path)))
        return ""

    prompt = DOCSTRING_SYSTEM_PROMPT + "\n\n" + source

    with console.status("[bold cyan]Generating docstrings...[/bold cyan]"):
        message = ask_llm(prompt)

    if looks_like_error(message):
        print_error(message)
        return ""

    docs = _extract_code_block(message.strip())
    if not docs:
        print_warning("the model returned an empty answer.")
        return ""

    _print_code(path, docs)

    if write and not write_docs(path, docs):
        return ""

    return docs
