"""Unit test generation command."""

import sys
from pathlib import Path
from typing import Optional

import typer
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

TESTS_DIR_NAME = "tests"
TEST_PREFIX = "test_"
BACKUP_SUFFIX = ".bak"


def _is_interactive() -> bool:
    """Return True when the command runs in an interactive terminal."""
    return sys.stdin.isatty()


def expected_test_path(source: Path) -> Path:
    """Return the default test module path for a source file.

    ``utils.py`` maps to ``tests/test_utils.py``. A file that is
    already named ``test_*.py`` keeps its name so the prefix is not
    doubled.

    The name intentionally avoids the ``test_`` prefix so pytest does
    not collect this helper as a test function.
    """
    stem = source.stem
    if not stem.startswith(TEST_PREFIX):
        stem = TEST_PREFIX + stem
    return Path(TESTS_DIR_NAME) / (stem + PYTHON_SUFFIX)


def _confirm_save(target: Path) -> bool:
    """Ask the user whether the generated tests should be written.

    Returns False when the terminal is not interactive, so scripted
    runs never block waiting for input.
    """
    if not _is_interactive():
        print_warning(
            "not an interactive terminal; rerun with --write to save the result"
        )
        return False
    return typer.confirm(f"Write the tests to {target}?", default=False)


def write_tests(target: Path, code: str) -> bool:
    """Create the tests directory when needed and save the test module.

    A ``.bak`` copy is made only when the target file already exists.

    Returns True when the file was written successfully.
    """
    backup: Optional[Path] = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            backup = target.with_name(target.name + BACKUP_SUFFIX)
            backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
        target.write_text(code + chr(10), encoding="utf-8")
    except OSError as exc:
        print_error("cannot write the file: " + str(exc))
        return False

    line = "[bold green]Saved[/bold green] " + escape(str(target))
    if backup is not None:
        line += " [dim](backup: " + escape(str(backup)) + ")[/dim]"
    console.print(line)
    return True


def generate_tests(
    file_path: str,
    out: Optional[str] = None,
    write: bool = False,
) -> str:
    """Generate a pytest module for the given Python source file.

    Args:
        file_path: Path to the Python file that needs tests.
        out: Optional output path; when omitted the file is written
            to ``tests/test_<name>.py``.
        write: When True, save the result without asking for
            confirmation.

    The generated module is printed to the console. When write is
    False and the terminal is interactive, the user is asked whether
    the test file should be created.

    Returns the generated test module, or an empty string when the
    file is missing, is not a Python file, or the request failed.
    """
    path = Path(file_path)
    if not require_file(path, kind="Python source"):
        return ""
    if path.suffix != PYTHON_SUFFIX:
        print_warning(
            "not a Python file: " + escape(str(path)) + "; pass a .py file"
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

    target = Path(out) if out else expected_test_path(path)
    print_code(target, tests)

    if not (write or _confirm_save(target)):
        console.print("[dim]Tests were not written.[/dim]")
        return tests

    if not write_tests(target, tests):
        return ""

    return tests
