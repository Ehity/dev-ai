"""Standup command: daily status reports from git history."""

import subprocess
from typing import List

from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel

from dev_ai.client import ask_llm
from dev_ai.commands._common import (
    console,
    is_git_repository,
    looks_like_error,
    print_error,
    print_warning,
)
from dev_ai.prompts import STANDUP_SYSTEM_PROMPT

SINCE = "1 day ago"


def _git_config(name: str) -> str:
    """Return a git config value, or an empty string when it is not set."""
    try:
        result = subprocess.run(
            ["git", "config", name],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def get_recent_commits() -> List[str]:
    """Return subject lines of the commits made during the last day.

    Commits are filtered by the configured git user.name. When the name is
    not set, all recent commits are used and a warning is printed.
    """
    if not is_git_repository():
        print_warning("the current directory is not a git repository.")
        return []

    author = _git_config("user.name")
    args = ["git", "log", "--since=" + SINCE]
    if author:
        args.append("--author=" + author)
    else:
        print_warning("git user.name is not set; showing commits from everyone.")

    try:
        result = subprocess.run(
            args + ["--pretty=format:%s"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print_warning("git is not installed or is not available in PATH.")
        return []

    if result.returncode != 0:
        detail = (result.stderr or "").strip()
        print_warning("git log failed: " + escape(detail))
        return []

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def standup() -> str:
    """Generate a Daily Standup report from the recent git commits.

    Collects the commits of the last day, asks the LLM to structure them
    into Done / Next / Blockers sections and prints the report inside a
    Rich panel.

    Returns:
        The report as Markdown, or an empty string when there are no
        commits or the request failed.
    """
    commits = get_recent_commits()
    if not commits:
        print_warning(
            "no commits found in the last day: commit your work first "
            "or run the command from the project root."
        )
        return ""

    listing = chr(10).join("- " + item for item in commits)
    prompt = (
        STANDUP_SYSTEM_PROMPT
        + "\n\nGit commits from the last day:\n"
        + listing
    )

    with console.status("[bold cyan]Preparing your standup...[/bold cyan]"):
        message = ask_llm(prompt)

    if looks_like_error(message):
        print_error(message)
        return ""

    report = message.strip()
    console.print(
        Panel(
            Markdown(report),
            title="Daily Standup",
            border_style="cyan",
        )
    )
    return report
