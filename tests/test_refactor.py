"""Unit tests for the refactor command (dev_ai.commands.refactor)."""

from pathlib import Path

from dev_ai.commands import refactor


def test_improvements_section_extracts():
    answer = (
        "some text\n## Improvements\n"
        "- Renamed foo to bar\n- Added type hints\n"
        "```python\nx = 1\n```"
    )
    result = refactor._improvements_section(answer)
    assert "## Improvements" in result
    assert "Renamed foo to bar" in result
    assert "Added type hints" in result


def test_improvements_section_no_marker():
    assert refactor._improvements_section("just some text") == ""


def test_improvements_section_handles_unclosed_fence():
    answer = "## Improvements\n- change\n```python\ny = 2"
    result = refactor._improvements_section(answer)
    assert "- change" in result
    assert "```" not in result


def test_write_refactor_creates_backup(tmp_path):
    """Existing file gets a .bak backup before being overwritten."""
    target = tmp_path / "sample.py"
    target.write_text("x = 1\n", encoding="utf-8")
    assert refactor.write_refactor(target, "x = 2")
    backup = tmp_path / "sample.py.bak"
    assert backup.read_text(encoding="utf-8") == "x = 1\n"
    assert target.read_text(encoding="utf-8") == "x = 2\n"


def test_write_refactor_returns_false_on_error(tmp_path, monkeypatch):
    """write_refactor returns False when writing fails."""
    target = tmp_path / "sample.py"

    def raise_oserror(*args, **kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr(refactor.console, "print", lambda *a, **k: None)
    monkeypatch.setattr(Path, "write_text", raise_oserror)
    assert refactor.write_refactor(target, "code\n") is False


def test_require_file_accepts_any_existing_file(tmp_path):
    """require_file returns True for any existing file (kind is informational only)."""
    target = tmp_path / "notes.txt"
    target.write_text("hello\n", encoding="utf-8")
    assert refactor.require_file(target, kind="source") is True


def test_read_source_returns_none_for_missing(tmp_path):
    """read_source returns None for a missing file."""
    assert refactor.read_source(tmp_path / "nope.py") is None
