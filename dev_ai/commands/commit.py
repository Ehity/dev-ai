"""Commit message generation command."""

import subprocess
from typing import List, Optional

from rich.console import Console
from rich.markup import escape
from rich.prompt import Confirm

from dev_ai.client import ask_llm
from dev_ai.prompts import COMMIT_SYSTEM_PROMPT

console = Console()

ERROR_PREFIXES = ("[config error]", "[network error]", "[api error]")


def _looks_like_error(message: str) -> bool:
    """Return True when ask_llm reported a configuration or API error."""
    return message.startswith(ERROR_PREFIXES)


def _is_git_repository() -> bool:
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


def _run_git_diff(args: List[str]) -> Optional[str]:
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
        message = (result.stderr or result.stdout or "").strip()
        console.print(
            "[bold yellow]Warning:[/bold yellow] git diff failed: " + escape(message)
        )
        return None

    return result.stdout


def get_staged_diff() -> str:
    """Return the staged changes (git diff --staged).

    Warns and returns an empty string when the index is empty or when
    the current directory is not a git repository.
    """
    if not _is_git_repository():
        console.print(
            "[bold yellow]Warning:[/bold yellow] the current directory "
            "is not a git repository."
        )
        return ""
    diff = _run_git_diff(["--staged"])
    if diff is None:
        return ""
    if not diff.strip():
        console.print(
            "[bold yellow]Warning:[/bold yellow] nothing staged yet; "
            "add files with [bold]git add[/bold] first."
        )
        return ""
    return diff


def get_unstaged_diff() -> str:
    """Return the unstaged changes (git diff).

    Warns and returns an empty string when there are no unstaged
    changes or when the current directory is not a git repository.
    """
    if not _is_git_repository():
        console.print(
            "[bold yellow]Warning:[/bold yellow] the current directory "
            "is not a git repository."
        )
        return ""
    diff = _run_git_diff([])
    if diff is None:
        return ""
    if not diff.strip():
        console.print("[bold yellow]Warning:[/bold yellow] no unstaged changes found.")
        return ""
    return diff


def generate_commit_message() -> str:
    """Generate a Conventional Commits message for the staged changes.

    Returns the generated message, or an empty string when there is
    nothing staged to describe.
    """
    diff = get_staged_diff()
    if not diff:
        return ""

    prompt = COMMIT_SYSTEM_PROMPT + "\n\n" + diff

    with console.status("[bold cyan]Generating commit message...[/bold cyan]"):
        message = ask_llm(prompt)

    if _looks_like_error(message):
        console.print("[bold red]" + escape(message) + "[/bold red]")
        return ""

    console.print(message)
    return message.strip()


def run_git_commit(message: str) -> bool:
    """Create a git commit with the given message.

    Returns True when the commit was created successfully.
    """
    try:
        result = subprocess.run(
            ["git", "commit", "-m", message],
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

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        console.print("[bold red]Error:[/bold red] git commit failed: " + escape(detail))
        return False

    console.print("[bold green]Committed[/bold green]")
    console.print(escape(result.stdout.strip()))
    return True


def commit() -> int:
    """Generate a message for the staged changes and create the commit.

    Returns a process exit code: 0 on success, 1 on failure.
    """
    message = generate_commit_message()
    if not message:
        return 1

    if not Confirm.ask(
        "Run git commit -m with this message?",
        default=True,
        console=console,
    ):
        console.print("[dim]Commit cancelled.[/dim]")
        return 0

    return 0 if run_git_commit(message) else 1
