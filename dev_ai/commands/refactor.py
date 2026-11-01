"""Refactor command: clean up and optimize Python source files."""

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
from dev_ai.display import print_markdown
from dev_ai.prompts import REFACTOR_SYSTEM_PROMPT

IMPROVEMENTS_MARKER = "## Improvements"
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
    return typer.confirm(f"Overwrite {path} with the refactored code?", default=False)


def write_refactor(path: Path, code: str) -> bool:
    """Write refactored code back to the file, keeping a backup copy.

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


def _improvements_section(answer: str) -> str:
    """Return the improvements section of the answer, or an empty string."""
    position = answer.find(IMPROVEMENTS_MARKER)
    if position == -1:
        return ""
    section = answer[position:]
    if section.count("```") % 2 != 0:
        section = section.split("```")[0]
    return section.strip()


def refactor_code(file_path: str, write: bool = False) -> str:
    """Refactor a Python file with the LLM and print the result.

    Reads the source file, asks the model for a refactored version and
    prints it with syntax highlighting, followed by the short list of
    improvements made.

    Args:
        file_path: Path to the Python file to refactor.
        write: When True, save the result without asking for
            confirmation and keep a backup copy next to the file.

    When write is False and the terminal is interactive, the user is
    asked whether the file should be updated.

    Returns:
        The refactored source code, or an empty string when the file
        cannot be read or the request failed.
    """
    path = Path(file_path)
    if not require_file(path, kind="source"):
        return ""

    source = read_source(path)
    if source is None:
        return ""
    if not source.strip():
        print_warning("the file is empty: " + escape(str(path)))
        return ""

    prompt = (
        REFACTOR_SYSTEM_PROMPT
        + "\n\nRefactor the following file: "
        + str(path)
        + "\n\n"
        + source
    )

    with console.status("[bold cyan]Refactoring the code...[/bold cyan]"):
        message = ask_llm(prompt)

    if looks_like_error(message):
        print_error(message)
        return ""

    answer = message.strip()
    code = extract_code_block(answer)
    if not code.strip():
        print_warning("the response did not contain a code block")
        print_error("unexpected response format; try again")
        return ""

    print_code(path, code)

    improvements = _improvements_section(answer)
    if improvements:
        print_markdown(improvements)

    if not (write or _confirm_overwrite(path)):
        console.print("[dim]File left unchanged.[/dim]")
        return code

    if not write_refactor(path, code):
        return ""

    return code
