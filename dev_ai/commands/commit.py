"""Commit message generation command."""

import subprocess

from rich.console import Console

from dev_ai.client import ask_llm
from dev_ai.prompts import COMMIT_SYSTEM_PROMPT

console = Console()


def get_staged_diff() -> str:
    """Return the staged git diff, or an empty string on failure."""
    result = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


def generate_commit_message() -> str:
    """Generate a Conventional Commits message for the staged changes."""

    diff = get_staged_diff()
    if not diff.strip():
        console.print("Nothing staged: run git add first.")
        return ""

    prompt = COMMIT_SYSTEM_PROMPT + "\n\n" + diff

    with console.status("Generating commit message..."):
        message = ask_llm(prompt)

    console.print(message)
    return message.strip()
