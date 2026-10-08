"""Refactor command: clean up and optimize Python source files."""

from pathlib import Path

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


def _improvements_section(answer: str) -> str:
    """Return the improvements section of the answer, or an empty string."""
    position = answer.find(IMPROVEMENTS_MARKER)
    if position == -1:
        return ""
    section = answer[position:]
    if section.count("```") % 2 != 0:
        section = section.split("```")[0]
    return section.strip()


def refactor_code(file_path: str) -> str:
    """Refactor a Python file with the LLM and print the result.

    Reads the source file, asks the model for a refactored version and
    prints it with syntax highlighting, followed by the short list of
    improvements made.

    Args:
        file_path: Path to the Python file to refactor.

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

    return code
