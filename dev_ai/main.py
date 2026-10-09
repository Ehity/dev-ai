"""dev-ai CLI entrypoint."""

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from dev_ai.commands.commit import commit as generate_and_commit
from dev_ai.commands.config import config as config_command_impl
from dev_ai.commands.doc import generate_docs
from dev_ai.commands.explain import explain_error
from dev_ai.commands.refactor import refactor_code
from dev_ai.commands.review import review_code
from dev_ai.commands.standup import standup as generate_standup
from dev_ai.commands.test_gen import generate_tests

app = typer.Typer(
    name="dev-ai",
    help="AI-powered CLI assistant for developers",
    no_args_is_help=True,
)


@app.callback()
def callback() -> None:
    """AI-powered CLI assistant for developers."""


console = Console()


@app.command()
def hello(
    name: str = typer.Option(
        "developer",
        "--name",
        "-n",
        help="Name to greet",
    ),
) -> None:
    """Print a greeting message."""
    console.print(
        Panel.fit(
            f"[bold green]Hello, {name}![/bold green]\n"
            "[dim]dev-ai — AI-powered CLI assistant[/dim]",
            title="dev-ai",
            border_style="cyan",
        )
    )
    console.print("[bold]Welcome![/bold] CLI is up and running.")


@app.command(name="commit")
def commit_command() -> None:
    """Generate a commit message for staged changes and commit them."""
    raise typer.Exit(code=generate_and_commit())


@app.command(name="review")
def review_command(
    file: Optional[str] = typer.Option(
        None,
        "--file",
        "-f",
        help="Path to the file to review; defaults to the current git diff",
    ),
) -> None:
    """Review a file or the uncommitted changes with the LLM."""
    raise typer.Exit(code=0 if review_code(file) else 1)


@app.command(name="doc")
def doc_command(
    file: str = typer.Option(
        ...,
        "--file",
        "-f",
        help="Path to the Python file that needs docstrings",
    ),
    write: bool = typer.Option(
        False,
        "--write",
        "-w",
        help="Overwrite the file without confirmation (keeps a .bak backup)",
    ),
) -> None:
    """Generate docstrings for a Python file and print the result."""
    raise typer.Exit(code=0 if generate_docs(file, write) else 1)


@app.command(name="test")
def test_command(
    file: str = typer.Option(
        ...,
        "--file",
        "-f",
        help="Path to the Python file that needs tests",
    ),
    out: Optional[str] = typer.Option(
        None,
        "--out",
        "-o",
        help="Where to save the tests (default: tests/test_<name>.py)",
    ),
    write: bool = typer.Option(
        False,
        "--write",
        "-w",
        help="Write the test file without confirmation",
    ),
) -> None:
    """Generate a pytest test module for a Python file."""
    raise typer.Exit(code=0 if generate_tests(file, out, write) else 1)


@app.command(name="config")
def config_command(
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="LLM model to use (saved to .env as DEV_AI_MODEL)",
    ),
    lang: Optional[str] = typer.Option(
        None,
        "--lang",
        "-l",
        help="Language of the AI answers (saved to .env as DEV_AI_LANG)",
    ),
) -> None:
    """Show or update the dev-ai settings stored in .env."""
    raise typer.Exit(code=config_command_impl(model, lang))


@app.command(name="explain")
def explain_command(
    error_input: Optional[str] = typer.Argument(
        None,
        help="Error text, traceback or log lines to analyse",
    ),
    file: Optional[str] = typer.Option(
        None,
        "--file",
        "-f",
        help="Read the error from this log file (takes priority over the argument)",
    ),
) -> None:
    """Explain an error message, log or stack trace with the LLM."""
    raise typer.Exit(code=0 if explain_error(error_input, file) else 1)


@app.command(name="refactor")
def refactor_command(
    file: str = typer.Option(
        ...,
        "--file",
        "-f",
        help="Path to the Python file to refactor",
    ),
) -> None:
    """Refactor a Python file and print the improved version."""
    raise typer.Exit(code=0 if refactor_code(file) else 1)


@app.command(name="standup")
def standup_command() -> None:
    """Generate a Daily Standup report from the recent git commits."""
    raise typer.Exit(code=0 if generate_standup() else 1)


if __name__ == "__main__":
    app()
