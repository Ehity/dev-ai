"""Unit tests for the export command (dev_ai.commands.export)."""

from pathlib import Path

from dev_ai.commands import export


def _sample_messages():
    return [
        {"role": "user", "content": "Hello, world!"},
        {"role": "assistant", "content": "Hi there!"},
    ]


def test_render_markdown_structure():
    content = export._render_markdown(_sample_messages(), "dev-ai_session.txt")
    assert "# dev-ai Export" in content
    assert "**Generated:**" in content
    assert "`dev-ai_session.txt`" in content
    assert "### User" in content
    assert "### Assistant" in content
    assert "Hello, world!" in content
    assert "Hi there!" in content


def test_render_markdown_empty():
    content = export._render_markdown([], "dev-ai_session.txt")
    assert "_No messages recorded yet._" in content


def test_render_json_is_valid_and_complete():
    import json

    content = export._render_json(_sample_messages(), "dev-ai_session.txt")
    payload = json.loads(content)
    assert payload["message_count"] == 2
    assert payload["source"] == "dev-ai_session.txt"
    assert payload["messages"] == _sample_messages()
    assert "generated" in payload


def test_render_txt_structure():
    content = export._render_txt(_sample_messages(), "dev-ai_session.txt")
    assert "dev-ai Export" in content
    assert "Generated:" in content
    assert "[USER]" in content
    assert "[ASSISTANT]" in content
    assert "Hello, world!" in content


def test_default_output_name():
    name = export._default_output("md")
    assert name.startswith("dev_ai_export_")
    assert name.endswith(".md")
    assert len(name.split("_")[-1].split(".")[0]) == 6  # HHMMSS


def test_read_session_ignores_blank_and_malformed(tmp_path):
    p = tmp_path / "dev-ai_session.txt"
    content = (
        "user: hi\n\n"
        "bad line without colon\n"
        "assistant: hello\n"
    )
    p.write_text(content, encoding="utf-8")
    history = export._read_session(p)
    assert history == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]


def test_read_session_missing_file(tmp_path):
    p = tmp_path / "nonexistent.txt"
    assert export._read_session(p) == []


def test_history_command_missing_file_is_empty():
    """A missing session file yields an empty history without raising."""
    import tempfile

    missing = Path(tempfile.mkdtemp()) / "does_not_exist.txt"
    history = export._read_session(missing)
    assert history == []

