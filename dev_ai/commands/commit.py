"""Commit message generation command."""

import subprocess
from typing import List, Optional

from rich.console import Console
from rich.markup import escape

from dev_ai.client import ask_llm
from dev_ai.prompts import COMMIT_SYSTEM_PROMPT

console = Console()


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

    console.print(message)
    return message.strip()
