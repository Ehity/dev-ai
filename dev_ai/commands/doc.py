"""Docstring generation command."""

import sys
from pathlib import Path

import typer
from rich.markup import escape

from dev_ai.client import ask_llm
from dev_ai.commands._common import (
    console,
    extract_code_block,
    looks_like_error,
    print_code,
    print_error,
    print_warning,
    read_source,
    require_file,
)
from dev_ai.prompts import DOCSTRING_SYSTEM_PROMPT

BACKUP_SUFFIX = ".bak"


def _is_interactive() -> bool:
    """Return True when the command runs in an interactive terminal."""
    return sys.stdin.isatty()


def _confirm_overwrite(path: Path) -> bool:
    """Ask the user whether the generated code should be saved.

    Returns False when the terminal is not interactive, so scripted
    runs never block waiting for input.
    """
    if not _is_interactive():
        print_warning(
            "not an interactive terminal; rerun with --write to save the result"
        )
        return False
    return typer.confirm(f"Overwrite {path} with the generated code?", default=False)


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
        write: When True, save the result without asking for
            confirmation and keep a backup copy next to the file.

    When write is False and the terminal is interactive, the user is
    asked whether the file should be updated.

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

    docs = extract_code_block(message.strip())
    if not docs:
        print_warning("the model returned an empty answer.")
        return ""

    print_code(path, docs)

    if not (write or _confirm_overwrite(path)):
        console.print("[dim]File left unchanged.[/dim]")
        return docs

    if not write_docs(path, docs):
        return ""

    return docs
