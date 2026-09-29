"""Console rendering helpers for dev-ai."""

from rich.console import Console
from rich.markdown import Markdown

console = Console()


def print_markdown(text: str) -> None:
    """Render Markdown text in the terminal."""
    console.print(Markdown(text))
