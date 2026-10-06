"""Configuration command: show and update dev-ai settings."""

import os
from typing import Dict, Optional

from rich.markup import escape
from rich.table import Table

from dev_ai import config as app_config
from dev_ai.commands._common import console, print_error, print_warning

# Map of CLI option -> environment variable written to .env.
SETTING_KEYS = {
    "model": "DEV_AI_MODEL",
    "lang": "DEV_AI_LANG",
}


def mask_key(key: str) -> str:
    """Return a display-safe version of an API key.

    The middle of the key is replaced with "***" so a few characters
    stay visible on both ends. An empty key is reported as not set.
    """
    if not key:
        return "not set"
    if len(key) <= 8:
        return key[0] + "***"
    visible = 4
    return key[:visible] + "***" + key[-visible:]


def build_config_table() -> Table:
    """Build a Rich table with the current dev-ai settings."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    table = Table(title="dev-ai configuration", border_style="cyan")
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    key_display = escape(mask_key(api_key))
    if not api_key:
        key_display = "[yellow]" + key_display + "[/yellow]"

    table.add_row("Model", escape(app_config.get_model()))
    table.add_row("Language", escape(app_config.get_language()))
    table.add_row("API key", key_display)
    table.add_row("API base URL", escape(app_config.get_base_url()))
    table.add_row("Env file", escape(str(app_config.ENV_FILE)))
    return table


def show_config() -> None:
    """Print the current settings as a table."""
    console.print(build_config_table())


def set_config(updates: Dict[str, str]) -> bool:
    """Persist the given settings to the .env file.

    Args:
        updates: Mapping of setting names ("model", "lang") to values.

    Returns:
        True when every setting was saved.
    """
    for name, value in updates.items():
        env_key = SETTING_KEYS.get(name)
        if env_key is None:
            print_warning("unknown setting ignored: " + escape(name))
            continue
        try:
            app_config.set_env_value(env_key, value)
        except OSError as exc:
            print_error("cannot write " + str(app_config.ENV_FILE) + ": " + str(exc))
            return False
        console.print(
            "[bold green]Saved[/bold green] "
            + escape(env_key)
            + "="
            + escape(value)
            + " [dim]in "
            + escape(str(app_config.ENV_FILE))
            + "[/dim]"
        )
    return True


def config(
    model: Optional[str] = None,
    lang: Optional[str] = None,
) -> int:
    """Show the current settings or update them.

    Args:
        model: New LLM model name, or None to keep the current one.
        lang: New response language, or None to keep the current one.

    Returns:
        0 on success, 1 when nothing could be saved.
    """
    updates: Dict[str, str] = {}
    if model is not None:
        updates["model"] = model.strip()
    if lang is not None:
        updates["lang"] = lang.strip()

    if updates:
        if not any(updates.values()):
            print_error("nothing to update: pass a value for --model or --lang.")
            return 1
        if not set_config(updates):
            return 1

    show_config()
    return 0
