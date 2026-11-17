"""Unit tests for the docstring generation command (dev_ai.commands.doc)."""

from pathlib import Path

from dev_ai.commands import doc


def test_write_docs_creates_backup(tmp_path):
    """Existing file gets a .bak backup before being overwritten."""
    target = tmp_path / "sample.py"
    target.write_text("x = 1\n", encoding="utf-8")
    assert doc.write_docs(target, "x = 2")
    backup = tmp_path / "sample.py.bak"
    assert backup.read_text(encoding="utf-8") == "x = 1\n"
    assert target.read_text(encoding="utf-8") == "x = 2\n"


def test_write_docs_returns_false_on_error(tmp_path, monkeypatch):
    """write_docs returns False when writing fails."""
    target = tmp_path / "sample.py"

    def raise_oserror(*args, **kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr(doc.console, "print", lambda *a, **k: None)
    monkeypatch.setattr(Path, "write_text", raise_oserror)
    assert doc.write_docs(target, "code\n") is False


def test_require_file_accepts_any_existing_file(tmp_path):
    """require_file returns True for any existing file."""
    target = tmp_path / "notes.txt"
    target.write_text("hello\n", encoding="utf-8")
    assert doc.require_file(target, kind="source") is True


def test_read_source_returns_none_for_missing(tmp_path):
    """read_source returns None for a missing file."""
    assert doc.read_source(tmp_path / "nope.py") is None


def test_generate_docs_returns_empty_for_missing_file(tmp_path):
    """generate_docs returns '' when the source file does not exist."""
    result = doc.generate_docs(str(tmp_path / "nope.py"))
    assert result == ""


def test_generate_docs_returns_empty_for_non_python(tmp_path):
    """generate_docs returns '' for a non-.py file."""
    not_py = tmp_path / "data.txt"
    not_py.write_text("not python\n", encoding="utf-8")
    result = doc.generate_docs(str(not_py))
    assert result == ""


def test_generate_docs_returns_empty_for_empty_file(tmp_path, monkeypatch):
    """generate_docs returns '' for an empty Python file."""
    empty = tmp_path / "empty.py"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setattr(doc.console, "print", lambda *a, **k: None)
    result = doc.generate_docs(str(empty))
    assert result == ""


def test_generate_docs_calls_llm_and_returns(monkeypatch, tmp_path):
    """generate_docs sends source to LLM and returns extracted docstrings."""
    source_file = tmp_path / "sample.py"
    source_file.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

    calls = []

    def fake_ask_llm(prompt, **kwargs):
        calls.append(prompt)
        return (
            "```python\n"
            "\"\"\"My module.\"\"\"\n"
            "def add(a, b):\n"
            '    """Add two numbers."""\n'
            "    return a + b\n"
            "```"
        )

    monkeypatch.setattr(doc, "ask_llm", fake_ask_llm)
    monkeypatch.setattr(doc.console, "print", lambda *a, **k: None)

    result = doc.generate_docs(str(source_file), write=True)
    assert len(calls) == 1
    assert "def add(a, b):" in calls[0]
    assert "\"\"\"My module.\"\"\"" in result
    assert "\"\"\"Add two numbers.\"\"\"" in result
