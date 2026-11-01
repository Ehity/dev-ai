"""Unit tests for display helpers (dev_ai.display)."""

from unittest.mock import MagicMock

from dev_ai import display


def test_print_markdown_renders(monkeypatch):
    fake_console = MagicMock()
    monkeypatch.setattr(display, "console", fake_console)

    display.print_markdown("# Hello")

    fake_console.print.assert_called_once()
    arg = fake_console.print.call_args[0][0]
    from rich.markdown import Markdown

    assert isinstance(arg, Markdown)


def test_print_markdown_empty(monkeypatch):
    fake_console = MagicMock()
    monkeypatch.setattr(display, "console", fake_console)

    display.print_markdown("")

    fake_console.print.assert_called_once()


def test_print_markdown_with_code_fence(monkeypatch):
    fake_console = MagicMock()
    monkeypatch.setattr(display, "console", fake_console)

    display.print_markdown("```python\nprint(1)\n```")

    fake_console.print.assert_called_once()
