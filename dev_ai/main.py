"""dev-ai CLI entrypoint."""

import typer
from rich.console import Console
from rich.panel import Panel

from dev_ai.commands.commit import commit as generate_and_commit

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


if __name__ == "__main__":
    app()
