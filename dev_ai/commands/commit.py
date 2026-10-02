"""Commit message generation command."""

import subprocess

from rich.markup import escape
from rich.prompt import Confirm

from dev_ai.client import ask_llm
from dev_ai.commands._common import (
    console,
    is_git_repository,
    looks_like_error,
    print_error,
    print_warning,
    run_git_diff,
)
from dev_ai.prompts import COMMIT_SYSTEM_PROMPT


def get_staged_diff(quiet: bool = False) -> str:
    """Return the staged changes (git diff --staged).

    Warns and returns an empty string when the index is empty or when
    the current directory is not a git repository. Pass quiet=True to
    skip the warning about an empty index.
    """
    if not is_git_repository():
        print_warning("the current directory is not a git repository.")
        return ""
    diff = run_git_diff(["--staged"])
    if diff is None:
        return ""
    if not diff.strip():
        if not quiet:
            print_warning(
                "nothing staged yet; add files with [bold]git add[/bold] first."
            )
        return ""
    return diff


def get_unstaged_diff(quiet: bool = False) -> str:
    """Return the unstaged changes (git diff).

    Warns and returns an empty string when there are no unstaged changes
    or when the current directory is not a git repository. Pass
    quiet=True to skip the warning about the missing changes.
    """
    if not is_git_repository():
        print_warning("the current directory is not a git repository.")
        return ""
    diff = run_git_diff([])
    if diff is None:
        return ""
    if not diff.strip():
        if not quiet:
            print_warning("no unstaged changes found.")
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

    if looks_like_error(message):
        print_error(message)
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
        print_warning("git is not installed or is not available in PATH.")
        return False

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        console.print(
            "[bold red]Error:[/bold red] git commit failed: " + escape(detail)
        )
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
