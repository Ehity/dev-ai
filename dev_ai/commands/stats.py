"""Stats command: show aggregated LLM API usage statistics."""

from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table

from dev_ai.commands._common import console
from dev_ai.services import usage_tracker


def stats(
    today: bool = typer.Option(
        False, "--today", help="Restrict the report to the current day"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Filter by a specific model name"
    ),
) -> int:
    """Show token usage statistics collected by the usage tracker.

    Args:
        today: When True, only records from today are counted.
        model: Optional model name to filter by.

    Returns:
        0 on success, 1 when no records match.
    """
    records = usage_tracker.query(today=today, model=model)

    if not records:
        console.print(
            "[dim]No usage records yet. Run a command that calls the "
            "LLM first (e.g. 'dev-ai ask \"hi\"').[/dim]"
        )
        return 1

    summary = usage_tracker.aggregate(records)

    # --- Summary card -------------------------------------------------
    scope_bits = []
    if today:
        scope_bits.append("today")
    if model:
        scope_bits.append(f"model={model}")
    scope = ", ".join(scope_bits) if scope_bits else "all time"

    console.print(
        Panel(
            f"[bold]Requests:[/bold] {summary['requests']}  "
            f"([green]{summary['requests'] - summary['errors']} ok[/green], "
            f"[red]{summary['errors']} errors[/red])\n"
            f"[bold]Input tokens:[/bold]  {summary['in']:,}\n"
            f"[bold]Output tokens:[/bold] {summary['out']:,}\n"
            f"[bold]Total tokens:[/bold]  {summary['total']:,}\n"
            f"[bold]Avg response:[/bold] {summary['avg_ms']} ms",
            title=f"dev-ai usage ({scope})",
            border_style="cyan",
        )
    )

    # --- Per-model breakdown -----------------------------------------
    by_model: dict = {}
    for rec in records:
        name = str(rec.get("model", "?"))
        by_model.setdefault(name, []).append(rec)

    if len(by_model) > 1 or model is None:
        table = Table(
            title="By model", show_header=True, header_style="bold cyan"
        )
        table.add_column("Model", style="cyan")
        table.add_column("Requests", justify="right")
        table.add_column("In", justify="right")
        table.add_column("Out", justify="right")
        table.add_column("Avg ms", justify="right")

        for name in sorted(by_model):
            agg = usage_tracker.aggregate(by_model[name])
            table.add_row(
                name,
                str(agg["requests"]),
                f"{agg['in']:,}",
                f"{agg['out']:,}",
                str(agg["avg_ms"]),
            )
        console.print(table)

    return 0


__all__ = ["stats"]
