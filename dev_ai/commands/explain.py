"""Explain command: analyse errors, logs and stack traces."""

from pathlib import Path
from typing import Optional

from dev_ai.client import ask_llm
from dev_ai.commands._common import (
    console,
    looks_like_error,
    print_error,
    print_warning,
    read_source,
    read_stdin,
    require_file,
)
from dev_ai.display import print_markdown
from dev_ai.prompts import EXPLAIN_SYSTEM_PROMPT

USAGE_HINT = (
    "nothing to explain; pass the error text as an argument, pipe it via "
    "stdin (cat error.log | dev-ai explain), or use --file <path>"
)


def _error_request(error_input: Optional[str], file: Optional[str]) -> Optional[str]:
    """Build the explain request, or None when there is nothing to analyse.

    When *file* is given it has priority over *error_input*.
    """
    if file is not None:
        path = Path(file)
        if not require_file(path, kind="log"):
            return None
        text = read_source(path)
        if text is None:
            return None
        if not text.strip():
            print_warning("the file is empty: " + str(path))
            return None
        return "Error output read from " + str(path) + ":\n\n" + text

    piped = read_stdin().strip()
    parts = [text for text in ((error_input or "").strip(), piped) if text]
    if not parts:
        print_error(USAGE_HINT)
        return None

    return "Error output:\n\n" + "\n\n".join(parts)


def explain_error(error_input: Optional[str] = None, file: Optional[str] = None) -> str:
    """Analyse an error message or log file and print an explanation.

    Args:
        error_input: Raw error text, traceback or log lines passed on the
            command line.
        file: Path to a log file containing the error. When given, it takes
            priority over error_input.

    Returns:
        The explanation as Markdown, or an empty string when there was
        nothing to explain or the request failed.
    """
    request = _error_request(error_input, file)
    if request is None:
        return ""

    prompt = EXPLAIN_SYSTEM_PROMPT + "\n\n" + request

    with console.status("[bold cyan]Analyzing the error...[/bold cyan]"):
        message = ask_llm(prompt)

    if looks_like_error(message):
        print_error(message)
        return ""

    explanation = message.strip()
    print_markdown(explanation)
    return explanation
