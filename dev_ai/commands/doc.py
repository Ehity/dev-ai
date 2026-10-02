"""Docstring generation command."""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.syntax import Syntax

from dev_ai.client import ask_llm
from dev_ai.prompts import DOCSTRING_SYSTEM_PROMPT

console = Console()

ERROR_PREFIXES = ("[config error]", "[network error]", "[api error]")


def _looks_like_error(message: str) -> bool:
    """Return True when ask_llm reported a configuration or API error."""
    return message.startswith(ERROR_PREFIXES)


def _read_source(path: Path) -> Optional[str]:
    """Read the file as UTF-8 text, or None when it is not readable."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        console.print(
            "[bold red]Error:[/bold red] cannot read the file: " + escape(str(exc))
        )
        return None


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


def generate_docs(file_path: str) -> str:
    """Generate docstrings for the given Python source file.

    Returns the updated source, or an empty string when the file is
    missing or the request failed.
    """
    path = Path(file_path)
    if not path.exists():
        console.print(
            "[bold red]Error:[/bold red] file not found: "
            + escape(str(path))
            + "; check the path and try again."
        )
        return ""
    if not path.is_file():
        console.print(
            "[bold red]Error:[/bold red] not a file: "
            + escape(str(path))
            + "; pass a path to a Python source file."
        )
        return ""

    source = _read_source(path)
    if source is None:
        return ""
    if not source.strip():
        console.print(
            "[bold yellow]Warning:[/bold yellow] the file is empty: "
            + escape(str(path))
        )
        return ""

    prompt = DOCSTRING_SYSTEM_PROMPT + "\n\n" + source

    with console.status("[bold cyan]Generating docstrings...[/bold cyan]"):
        message = ask_llm(prompt)

    if _looks_like_error(message):
        console.print("[bold red]" + escape(message) + "[/bold red]")
        return ""

    docs = _extract_code_block(message.strip())
    if not docs:
        console.print(
            "[bold yellow]Warning:[/bold yellow] the model returned an empty answer."
        )
        return ""

    _print_code(path, docs)
    return docs
