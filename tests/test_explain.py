"""Unit tests for the explain command (dev_ai.commands.explain)."""

from dev_ai.commands import explain


def test_explain_error_no_input(monkeypatch):
    """Empty string when neither argument, stdin nor --file is given."""
    monkeypatch.setattr(explain, "read_stdin", lambda: "")
    monkeypatch.setattr(explain.console, "print", lambda *a, **k: None)
    assert explain.explain_error() == ""


def test_explain_error_from_argument(monkeypatch):
    """Sends the argument to LLM and returns the explanation."""
    monkeypatch.setattr(explain, "read_stdin", lambda: "")
    monkeypatch.setattr(explain.console, "print", lambda *a, **k: None)

    calls = []

    def fake_ask_llm(prompt):
        calls.append(prompt)
        return "The error means X."

    monkeypatch.setattr(explain, "ask_llm", fake_ask_llm)
    result = explain.explain_error("TypeError: unsupported operand")
    assert len(calls) == 1
    assert "TypeError: unsupported operand" in calls[0]
    assert result == "The error means X."


def test_explain_error_from_stdin(monkeypatch):
    """Sends piped stdin to LLM when no argument is given."""
    monkeypatch.setattr(explain, "read_stdin", lambda: "Traceback ...")
    monkeypatch.setattr(explain.console, "print", lambda *a, **k: None)

    calls = []

    def fake_ask_llm(prompt):
        calls.append(prompt)
        return "Here is why"

    monkeypatch.setattr(explain, "ask_llm", fake_ask_llm)
    result = explain.explain_error(None)
    assert len(calls) == 1
    assert "Traceback ..." in calls[0]
    assert result == "Here is why"


def test_explain_error_joins_argument_and_stdin(monkeypatch):
    """Joins argument and piped input into a single request."""
    monkeypatch.setattr(explain, "read_stdin", lambda: "line 2")
    monkeypatch.setattr(explain.console, "print", lambda *a, **k: None)

    calls = []

    def fake_ask_llm(prompt):
        calls.append(prompt)
        return "Fixed"

    monkeypatch.setattr(explain, "ask_llm", fake_ask_llm)
    result = explain.explain_error("line 1")
    assert len(calls) == 1
    assert "line 1" in calls[0]
    assert "line 2" in calls[0]
    assert result == "Fixed"


def test_explain_error_from_file(monkeypatch, tmp_path):
    """Reads the error from --file when it is provided."""
    log = tmp_path / "error.log"
    log.write_text("ValueError: bad\n", encoding="utf-8")
    monkeypatch.setattr(explain.console, "print", lambda *a, **k: None)

    calls = []

    def fake_ask_llm(prompt):
        calls.append(prompt)
        return "Check value"

    monkeypatch.setattr(explain, "ask_llm", fake_ask_llm)
    result = explain.explain_error(None, file=str(log))
    assert len(calls) == 1
    assert str(log) in calls[0]
    assert "ValueError: bad" in calls[0]
    assert result == "Check value"


def test_explain_error_llm_error(monkeypatch):
    """Returns '' when the LLM reports an error."""
    monkeypatch.setattr(explain, "read_stdin", lambda: "")
    monkeypatch.setattr(explain, "ask_llm", lambda prompt: "[api error] boom")
    monkeypatch.setattr(explain.console, "print", lambda *a, **k: None)
    assert explain.explain_error("Hello") == ""
