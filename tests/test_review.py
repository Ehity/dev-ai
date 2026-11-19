"""Unit tests for the review command (dev_ai.commands.review)."""

from dev_ai.commands import review


def test_read_file_returns_text(tmp_path):
    """_read_file returns UTF-8 text for a small valid file."""
    target = tmp_path / "sample.py"
    target.write_text("x = 1\n", encoding="utf-8", newline="")
    assert review._read_file(target) == "x = 1\n"


def test_read_file_none_for_missing(tmp_path):
    """_read_file returns None for a missing file."""
    assert review._read_file(tmp_path / "nope.py") is None


def test_read_file_none_for_binary(tmp_path):
    """_read_file returns None for a binary file."""
    target = tmp_path / "image.bin"
    target.write_bytes(b"\x00\x01\x02\x03")
    assert review._read_file(target) is None


def test_read_file_none_for_too_large(tmp_path, monkeypatch):
    """_read_file returns None when the file exceeds MAX_FILE_SIZE."""
    monkeypatch.setattr(review, "MAX_FILE_SIZE", 10)
    target = tmp_path / "big.py"
    target.write_text("x = 1\n" * 10, encoding="utf-8", newline="")
    assert review._read_file(target) is None


def test_read_file_none_for_invalid_utf8(tmp_path):
    """_read_file returns None for non-UTF-8 content."""
    target = tmp_path / "bad.py"
    target.write_bytes(b"\xff\xfe")
    assert review._read_file(target) is None


def test_file_request_none_for_missing(tmp_path):
    """_file_request returns None when the file does not exist."""
    assert review._file_request(tmp_path / "nope.py") is None


def test_file_request_none_for_empty(tmp_path, monkeypatch):
    """_file_request returns None for an empty file."""
    target = tmp_path / "empty.py"
    target.write_text("", encoding="utf-8")
    monkeypatch.setattr(review.console, "print", lambda *a, **k: None)
    assert review._file_request(target) is None


def test_file_request_returns_text(tmp_path, monkeypatch):
    """_file_request returns a prefixed request string."""
    target = tmp_path / "sample.py"
    target.write_text("x = 1\n", encoding="utf-8", newline="")
    monkeypatch.setattr(review.console, "print", lambda *a, **k: None)
    result = review._file_request(target)
    assert result == "Review the following file: " + str(target) + "\n\nx = 1\n"


def test_diff_request_none_when_no_changes(monkeypatch):
    """_diff_request returns None when there are no staged or unstaged changes."""
    monkeypatch.setattr(review, "get_staged_diff", lambda quiet: "")
    monkeypatch.setattr(review, "get_unstaged_diff", lambda quiet: "")
    monkeypatch.setattr(review.console, "print", lambda *a, **k: None)
    assert review._diff_request() is None


def test_diff_request_returns_text(monkeypatch):
    """_diff_request returns a prefixed request when there are changes."""
    monkeypatch.setattr(review, "get_staged_diff", lambda quiet: "diff content")
    monkeypatch.setattr(review.console, "print", lambda *a, **k: None)
    result = review._diff_request()
    expected = "Review the following git diff of uncommitted changes:\n\ndiff content"
    assert result == expected


def test_review_code_none_for_missing_file(tmp_path, monkeypatch):
    """review_code returns '' when the file does not exist."""
    monkeypatch.setattr(review.console, "print", lambda *a, **k: None)
    result = review.review_code(str(tmp_path / "nope.py"))
    assert result == ""


def test_review_code_calls_llm_and_returns(monkeypatch, tmp_path):
    """review_code sends the request to LLM and returns the review text."""
    source_file = tmp_path / "sample.py"
    source_file.write_text("def foo():\n    pass\n", encoding="utf-8")

    calls = []

    def fake_ask_llm(prompt):
        calls.append(prompt)
        return "Looks good."

    monkeypatch.setattr(review, "ask_llm", fake_ask_llm)
    monkeypatch.setattr(review.console, "print", lambda *a, **k: None)

    result = review.review_code(str(source_file))
    assert len(calls) == 1
    assert "def foo():" in calls[0]
    assert result == "Looks good."
