"""Smoke test for session save/load in interactive mode."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from dev_ai.commands.interactive import (
    MAX_HISTORY,
    SESSION_FILE,
    _load_session,
    _offer_to_load_session,
    _save_session,
)


def test_save_load_roundtrip():
    """Save and load a session; the loaded history must match."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "session.txt"
        original = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I am fine."},
        ]
        _save_session(path, original)
        loaded = _load_session(path)
        assert loaded == original, f"Roundtrip failed: {loaded} != {original}"
        print("OK save_load_roundtrip")


def test_load_empty_file():
    """Loading an empty file returns an empty list."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "empty.txt"
        path.write_text("")
        assert _load_session(path) == []
        print("OK load_empty_file")


def test_load_skips_bad_lines():
    """Lines without a valid role are skipped."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "bad.txt"
        path.write_text("garbage\nuser: ok\n\nassistant: ok\n")
        loaded = _load_session(path)
        assert loaded == [
            {"role": "user", "content": "ok"},
            {"role": "assistant", "content": "ok"},
        ]
        print("OK load_skips_bad_lines")


def test_offer_load_no_file():
    """When no session file exists, returns empty list."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "nope.txt"
        assert _offer_to_load_session(path) == []
        print("OK offer_load_no_file")


def test_offer_load_with_file():
    """When a session file exists and user confirms, loads it."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "session.txt"
        path.write_text("user: question\nassistant: answer\n")
        with patch("rich.prompt.Confirm.ask", return_value=True):
            history = _offer_to_load_session(path)
        assert len(history) == 2
        assert history[0]["content"] == "question"
        assert history[1]["content"] == "answer"
        print("OK offer_load_with_file")


def test_offer_load_user_declined():
    """When user declines, returns empty list."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "session.txt"
        path.write_text("user: question\n")
        with patch("rich.prompt.Confirm.ask", return_value=False):
            assert _offer_to_load_session(path) == []
        print("OK offer_load_user_declined")


def test_offer_load_corrupt_file():
    """A corrupt file does not crash; returns empty list."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "corrupt.txt"
        path.write_bytes(b"\xff\xfe\x00\x00\x00")
        with patch("rich.prompt.Confirm.ask", return_value=True):
            assert _offer_to_load_session(path) == []
        print("OK offer_load_corrupt_file")


def test_session_file_constant():
    """SESSION_FILE is a Path."""
    assert isinstance(SESSION_FILE, Path)
    assert SESSION_FILE.name == "dev-ai_session.txt"
    print("OK session_file_constant")


def test_max_history_constant():
    """MAX_HISTORY is a positive integer."""
    assert isinstance(MAX_HISTORY, int)
    assert MAX_HISTORY > 0
    print("OK max_history_constant")


if __name__ == "__main__":
    test_save_load_roundtrip()
    test_load_empty_file()
    test_load_skips_bad_lines()
    test_offer_load_no_file()
    test_offer_load_with_file()
    test_offer_load_user_declined()
    test_offer_load_corrupt_file()
    test_session_file_constant()
    test_max_history_constant()
    print("RESULT ALL_OK")