"""Unit tests for the shared helpers in dev_ai.commands._common."""

import sys

import pytest

from dev_ai.commands._common import (
    ERROR_PREFIXES,
    extract_code_block,
    is_git_repository,
    looks_like_error,
    read_source,
    read_stdin,
    require_file,
    run_git_diff,
)


@pytest.mark.parametrize(
    "message",
    [
        "[config error] missing key",
        "[network error] timeout",
        "[api error] HTTP 500",
    ],
)
def test_looks_like_error_detects_client_errors(message):
    assert looks_like_error(message) is True


@pytest.mark.parametrize("message", ["", "all good", "Error: something"])
def test_looks_like_error_ignores_normal_text(message):
    assert looks_like_error(message) is False


def test_error_prefixes_are_known():
    assert "[config error]" in ERROR_PREFIXES


def test_extract_code_block_strips_python_fence():
    text = "Some text\n```python\ndef f():\n    return 1\n```\nMore text"
    assert extract_code_block(text) == "def f():\n    return 1"


def test_extract_code_block_without_fence_returns_text():
    assert extract_code_block("plain answer") == "plain answer"


def test_extract_code_block_handles_unclosed_fence():
    text = "```\nvalue = 1"
    result = extract_code_block(text)
    assert "value = 1" in result


def test_read_source_returns_text(tmp_path):
    target = tmp_path / "sample.py"
    target.write_text("x = 1\n", encoding="utf-8")
    assert read_source(target) == "x = 1\n"


def test_read_source_returns_none_for_missing_file(tmp_path):
    assert read_source(tmp_path / "missing.py") is None


def test_require_file_accepts_existing_file(tmp_path):
    target = tmp_path / "sample.py"
    target.write_text("x = 1\n", encoding="utf-8")
    assert require_file(target) is True


def test_require_file_rejects_directory(tmp_path):
    assert require_file(tmp_path) is False


def test_require_file_rejects_missing_path(tmp_path):
    assert require_file(tmp_path / "nope.py") is False


def test_read_stdin_returns_empty_for_tty(monkeypatch):
    class FakeTTY:
        def isatty(self):
            return True

        def read(self):  # pragma: no cover - must never be called
            raise AssertionError("stdin must not be read in an interactive shell")

    monkeypatch.setattr(sys, "stdin", FakeTTY())
    assert read_stdin() == ""


def test_read_stdin_returns_empty_when_unavailable(monkeypatch):
    monkeypatch.setattr(sys, "stdin", None)
    assert read_stdin() == ""


def test_read_stdin_reads_piped_stream(monkeypatch):
    class FakePipe:
        def isatty(self):
            return False

        def read(self):
            return "piped text"

    monkeypatch.setattr(sys, "stdin", FakePipe())
    assert read_stdin() == "piped text"


def test_is_git_repository_detects_work_tree():
    # The project itself is a git repository, so the helper must find it.
    assert is_git_repository() is True


def test_run_git_diff_returns_text():
    diff = run_git_diff(["--staged"])
    assert diff is None or isinstance(diff, str)
