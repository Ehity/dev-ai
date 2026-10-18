"""Export command: save session history and LLM responses to local files.

Supported formats: Markdown (default), JSON, plain TXT.
Output file defaults to dev_ai_export_YYYYMMDD_HHMMSS.<ext> when -o/--output
is not provided.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich.panel import Panel

from dev_ai.commands._common import console

export_app = typer.Typer(
    name="export",
    help="Export saved session history and LLM responses to MD/JSON/TXT.",
    no_args_is_help=True,
)

SESSION_FILE = "dev-ai_session.txt"


def _read_session(path: Path) -> List[dict]:
    """Read a saved session file into a list of {role, content} messages."""
    history: List[dict] = []
    if not path.exists():
        return history
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        role, _, content = stripped.partition(": ")
        if role in ("user", "assistant"):
            history.append({"role": role, "content": content})
    return history


def _default_output(ext: str) -> str:
    """Generate an auto-named output file path."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"dev_ai_export_{ts}.{ext}"


def _render_markdown(messages: List[dict], source: str) -> str:
    """Render history as a formatted Markdown document."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = []
    lines.append("# dev-ai Export")
    lines.append("")
    lines.append(f"**Generated:** {ts}")
    lines.append(f"**Source:** `{source}`")
    lines.append("")
    lines.append("## Session History")
    lines.append("")
    if not messages:
        lines.append("_No messages recorded yet._")
    for msg in messages:
        role = msg.get("role", "?")
        content = msg.get("content", "").strip()
        lines.append(f"### {role.title()}")
        lines.append("")
        lines.append("```text")
        lines.append(content)
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def _render_json(messages: List[dict], source: str) -> str:
    """Render history as a valid JSON document."""
    payload = {
        "generated": datetime.now().isoformat(),
        "source": source,
        "message_count": len(messages),
        "messages": messages,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _render_txt(messages: List[dict], source: str) -> str:
    """Render history as plain text."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = []
    lines.append("dev-ai Export")
    lines.append(f"Generated: {ts}")
    lines.append(f"Source: {source}")
    lines.append("")
    lines.append("SESSION HISTORY")
    lines.append("=" * 40)
    lines.append("")
    if not messages:
        lines.append("(no messages recorded yet)")
    for msg in messages:
        role = msg.get("role", "?").upper()
        content = msg.get("content", "").strip()
        lines.append(f"[{role}]")
        lines.append(content)
        lines.append("")
    return "\n".join(lines)


@export_app.command("history")
def export_history(
    fmt: str = typer.Option(
        "md",
        "--format",
        "-fmt",
        help="Output format: md, json, txt",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: auto-generated dev_ai_export_*.<ext>)",
    ),
) -> None:
    """Export the saved interactive session history to a file."""
    fmt = fmt.strip().lower()
    if fmt not in ("md", "json", "txt"):
        console.print(
            f"[bold red]Error:[/bold red] unsupported format '{fmt}'; "
            "use md, json or txt."
        )
        raise typer.Exit(code=1)

    session_path = Path(SESSION_FILE)
    messages = _read_session(session_path)

    if output:
        out_path = Path(output)
    else:
        ext = fmt
        out_path = Path(_default_output(ext))

    if out_path.exists():
        console.print(
            f"[bold yellow]Warning:[/bold yellow] overwriting existing "
            f"file {out_path}"
        )

    if fmt == "json":
        content = _render_json(messages, str(session_path))
    elif fmt == "txt":
        content = _render_txt(messages, str(session_path))
    else:
        content = _render_markdown(messages, str(session_path))

    out_path.write_text(content, encoding="utf-8")
    size = out_path.stat().st_size

    console.print(
        Panel(
            f"[bold green]Export complete.[/bold green]\n"
            f"File: {out_path.resolve()}\n"
            f"Format: {fmt.upper()}\n"
            f"Messages: {len(messages)}\n"
            f"Size: {size} bytes",
            title="dev-ai export",
            border_style="green",
        )
    )
