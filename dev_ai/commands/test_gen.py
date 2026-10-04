"""Unit test generation command."""

from pathlib import Path

from rich.markup import escape

from dev_ai.client import ask_llm
from dev_ai.commands._common import (
    PYTHON_SUFFIX,
    console,
    extract_code_block,
    looks_like_error,
    print_code,
    print_error,
    print_warning,
    read_source,
    require_file,
)
from dev_ai.prompts import UNIT_TEST_SYSTEM_PROMPT


def generate_tests(file_path: str) -> str:
    """Generate a pytest module for the given Python source file.

    Args:
        file_path: Path to the Python file that needs tests.

    Returns the generated test module, or an empty string when the
    file is missing, is not a Python file, or the request failed.
    """
    path = Path(file_path)
    if not require_file(path, kind="Python source"):
        return ""
    if path.suffix != PYTHON_SUFFIX:
        print_warning(
            "not a Python file: "
            + escape(str(path))
            + "; pass a .py file"
        )
        return ""

    source = read_source(path)
    if source is None:
        return ""
    if not source.strip():
        print_warning("the file is empty: " + escape(str(path)))
        return ""

    prompt = UNIT_TEST_SYSTEM_PROMPT + "\n\n" + source

    with console.status("[bold cyan]Generating unit tests...[/bold cyan]"):
        message = ask_llm(prompt)

    if looks_like_error(message):
        print_error(message)
        return ""

    tests = extract_code_block(message.strip())
    if not tests:
        print_warning("the model returned an empty answer.")
        return ""

    print_code(path, tests)
    return tests
