"""Unit tests for the test generation command (dev_ai.commands.test_gen)."""

from pathlib import Path

from dev_ai.commands import test_gen


def test_expected_test_path_plain_module(tmp_path):
    """utils.py maps to tests/test_utils.py."""
    result = test_gen.expected_test_path(tmp_path / "utils.py")
    assert result == Path("tests/test_utils.py")


def test_expected_test_path_test_module_keeps_name(tmp_path):
    """test_foo.py maps to tests/test_foo.py (no doubled prefix)."""
    result = test_gen.expected_test_path(tmp_path / "test_foo.py")
    assert result == Path("tests/test_foo.py")


def test_write_tests_creates_file(tmp_path):
    """write_tests writes the code to the target path."""
    target = tmp_path / "tests" / "test_sample.py"
    assert test_gen.write_tests(target, "def test_x():\n    assert True")
    assert target.read_text(encoding="utf-8") == "def test_x():\n    assert True\n"


def test_write_tests_creates_backup_when_exists(tmp_path):
    """An existing target file gets a .bak backup before being overwritten."""
    target = tmp_path / "tests" / "test_sample.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("old content\n", encoding="utf-8")
    assert test_gen.write_tests(target, "new content")
    backup = tmp_path / "tests" / "test_sample.py.bak"
    assert backup.read_text(encoding="utf-8") == "old content\n"
    assert target.read_text(encoding="utf-8") == "new content\n"


def test_write_tests_returns_false_on_error(tmp_path, monkeypatch):
    """write_tests returns False when the directory cannot be created."""
    target = tmp_path / "tests" / "test_sample.py"

    def raise_oserror(*args, **kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr(test_gen.console, "print", lambda *a, **k: None)
    monkeypatch.setattr(Path, "mkdir", raise_oserror)
    assert test_gen.write_tests(target, "code\n") is False


def test_generate_tests_returns_empty_for_missing_file(tmp_path):
    """generate_tests returns '' when the source file does not exist."""
    result = test_gen.generate_tests(str(tmp_path / "nope.py"))
    assert result == ""


def test_generate_tests_returns_empty_for_non_python(tmp_path):
    """generate_tests returns '' for a non-.py file."""
    not_py = tmp_path / "data.txt"
    not_py.write_text("not python\n", encoding="utf-8")
    result = test_gen.generate_tests(str(not_py))
    assert result == ""


def test_generate_tests_returns_empty_for_empty_file(tmp_path, monkeypatch):
    """generate_tests returns '' for an empty Python file."""
    empty = tmp_path / "empty.py"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setattr(test_gen.console, "print", lambda *a, **k: None)
    result = test_gen.generate_tests(str(empty))
    assert result == ""


def test_generate_tests_calls_llm_and_returns(monkeypatch, tmp_path):
    """generate_tests sends source to LLM and returns extracted tests."""
    source_file = tmp_path / "sample.py"
    source_file.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

    calls = []

    def fake_ask_llm(prompt, **kwargs):
        calls.append(prompt)
        return "```python\ndef test_add():\n    assert add(1, 2) == 3\n```"

    monkeypatch.setattr(test_gen, "ask_llm", fake_ask_llm)
    monkeypatch.setattr(test_gen.console, "print", lambda *a, **k: None)

    result = test_gen.generate_tests(str(source_file), write=True)
    assert len(calls) == 1
    assert "def add(a, b):" in calls[0]
    assert "def test_add():" in result
    assert "assert add(1, 2) == 3" in result
