"""Template command: manage saved prompt templates.

Templates are stored in a local JSON file (dev-ai_templates.json) so a
developer can keep frequently used prompts and replay them with one line.
"""

import json
from typing import Dict, Optional

import typer
from rich.table import Table

from dev_ai.client import ask_llm
from dev_ai.commands._common import console, looks_like_error, print_error
from dev_ai.display import print_markdown

TEMPLATES_FILE = "dev-ai_templates.json"

template_app = typer.Typer(
    name="template",
    help="Save, list, run and remove custom prompt templates.",
    no_args_is_help=True,
)


def _load_templates() -> Dict[str, str]:
    """Read the template store; missing or broken files yield {}."""
    try:
        with open(TEMPLATES_FILE, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def _save_templates(templates: Dict[str, str]) -> None:
    """Persist the template store as pretty-printed JSON."""
    with open(TEMPLATES_FILE, "w", encoding="utf-8") as fh:
        json.dump(templates, fh, ensure_ascii=False, indent=2, sort_keys=True)


@template_app.command("add")
def add_template(
    name: str = typer.Argument(..., help="Unique name of the template"),
    prompt: str = typer.Argument(..., help="Prompt text to store"),
) -> None:
    """Save a new prompt template under NAME."""
    templates = _load_templates()
    exists = name in templates
    templates[name] = prompt
    _save_templates(templates)
    verb = "Updated" if exists else "Saved"
    console.print(
        f"[green]{verb} template[/green] [bold]{name}[/bold] "
        f"in {TEMPLATES_FILE}"
    )


@template_app.command("list")
def list_templates() -> None:
    """Show every saved template in a table."""
    templates = _load_templates()
    if not templates:
        console.print(
            "[dim]No templates saved yet. Add one with: "
            "dev-ai template add <name> \"<prompt>\"[/dim]"
        )
        return

    table = Table(
        title="Prompt templates", show_header=True, header_style="bold cyan"
    )
    table.add_column("Name", style="cyan")
    table.add_column("Prompt")

    for name in sorted(templates):
        prompt = templates[name]
        if len(prompt) > 70:
            prompt = prompt[:67] + "..."
        table.add_row(name, prompt)

    console.print(table)


@template_app.command("run")
def run_template(
    name: str = typer.Argument(..., help="Name of the template to run"),
    extra: Optional[str] = typer.Argument(
        None, help="Extra text appended to the template prompt"
    ),
) -> None:
    """Send the stored template (plus extra text) to the LLM."""
    templates = _load_templates()
    if name not in templates:
        console.print(
            f"[bold red]Error:[/bold red] template not found: {name}; "
            "run 'dev-ai template list' to see saved names."
        )
        raise typer.Exit(code=1)

    prompt = templates[name]
    if extra and extra.strip():
        prompt = f"{prompt}\n\n{extra.strip()}"

    with console.status("[bold cyan]Thinking...[/bold cyan]"):
        message = ask_llm(prompt)

    if looks_like_error(message):
        print_error(message)
        raise typer.Exit(code=1)

    print_markdown(message.strip())


@template_app.command("remove")
def remove_template(
    name: str = typer.Argument(..., help="Name of the template to delete"),
) -> None:
    """Delete a saved template."""
    templates = _load_templates()
    if name not in templates:
        console.print(
            f"[bold red]Error:[/bold red] template not found: {name}; "
            "run 'dev-ai template list' to see saved names."
        )
        raise typer.Exit(code=1)

    del templates[name]
    _save_templates(templates)
    console.print(
        f"[green]Removed template[/green] [bold]{name}[/bold] "
        f"from {TEMPLATES_FILE}"
    )


__all__ = [
    "template_app",
    "add_template",
    "list_templates",
    "run_template",
    "remove_template",
]
