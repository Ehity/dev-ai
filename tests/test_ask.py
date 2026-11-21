"""Unit tests for the ask command (dev_ai.commands.ask)."""

from dev_ai.commands import ask


def test_ask_question_no_input(monkeypatch):
    """Empty string when neither argument nor piped input is present."""
    monkeypatch.setattr(ask.console, "print", lambda *a, **k: None)
    assert ask.ask_question(None) == ""


def test_ask_question_from_argument(monkeypatch):
    """Sends the argument to LLM and returns the answer."""
    monkeypatch.setattr(ask, "read_stdin", lambda: "")
    monkeypatch.setattr(ask.console, "print", lambda *a, **k: None)

    calls = []

    def fake_ask_llm(prompt):
        calls.append(prompt)
        return "Answer"

    monkeypatch.setattr(ask, "ask_llm", fake_ask_llm)
    result = ask.ask_question("What is Python?")
    assert calls == ["What is Python?"]
    assert result == "Answer"


def test_ask_question_from_stdin(monkeypatch):
    """Sends piped stdin to LLM when no argument is given."""
    monkeypatch.setattr(ask, "read_stdin", lambda: "explain this error")
    monkeypatch.setattr(ask.console, "print", lambda *a, **k: None)

    calls = []

    def fake_ask_llm(prompt):
        calls.append(prompt)
        return "Here is why"

    monkeypatch.setattr(ask, "ask_llm", fake_ask_llm)
    result = ask.ask_question(None)
    assert calls == ["explain this error"]
    assert result == "Here is why"


def test_ask_question_joins_argument_and_stdin(monkeypatch):
    """Joins argument and piped input into a single prompt."""
    monkeypatch.setattr(ask, "read_stdin", lambda: "stack trace")
    monkeypatch.setattr(ask.console, "print", lambda *a, **k: None)

    calls = []

    def fake_ask_llm(prompt):
        calls.append(prompt)
        return "Fixed"

    monkeypatch.setattr(ask, "ask_llm", fake_ask_llm)
    result = ask.ask_question("Explain:")
    assert calls == ["Explain:\n\nstack trace"]
    assert result == "Fixed"


def test_ask_question_llm_error(monkeypatch):
    """Returns '' when the LLM reports an error."""
    monkeypatch.setattr(ask, "read_stdin", lambda: "")
    monkeypatch.setattr(ask, "ask_llm", lambda prompt: "[api error] boom")
    monkeypatch.setattr(ask.console, "print", lambda *a, **k: None)
    assert ask.ask_question("Hello") == ""
