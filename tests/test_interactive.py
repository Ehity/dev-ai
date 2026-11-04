"""Unit tests for the interactive REPL (dev_ai.commands.interactive)."""

from dev_ai.commands import interactive


def test_exit_words_known():
    assert "exit" in interactive.EXIT_WORDS
    assert "quit" in interactive.EXIT_WORDS
    assert "q" in interactive.EXIT_WORDS


def test_max_history_default():
    assert interactive.MAX_HISTORY == 20


def test_save_session_writes_role_content_format(tmp_path):
    path = tmp_path / "dev-ai_session.txt"
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    interactive._save_session(path, history)
    text = path.read_text(encoding="utf-8")
    assert "user: Hello" in text
    assert "assistant: Hi there!" in text


def test_save_session_ends_with_newline(tmp_path):
    path = tmp_path / "dev-ai_session.txt"
    interactive._save_session(path, [{"role": "user", "content": "x"}])
    assert path.read_text(encoding="utf-8").endswith("\n")


def test_load_session_parses_correctly(tmp_path):
    path = tmp_path / "dev-ai_session.txt"
    path.write_text("user: hi\nassistant: hello\n", encoding="utf-8")
    history = interactive._load_session(path)
    assert history == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]


def test_load_session_skips_blank_and_malformed(tmp_path):
    path = tmp_path / "dev-ai_session.txt"
    path.write_text("user: hi\n\nbad line\nassistant: ok\n", encoding="utf-8")
    history = interactive._load_session(path)
    assert history == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "ok"},
    ]


def test_load_session_missing_file_raises(tmp_path):
    path = tmp_path / "nope.txt"
    try:
        interactive._load_session(path)
    except FileNotFoundError:
        pass
    else:  # pragma: no cover - must raise
        raise AssertionError("_load_session() must raise FileNotFoundError")


def test_handle_slash_command_unknown(tmp_path, monkeypatch, capsys):
    history = [{"role": "user", "content": "x"}]
    handled, model = interactive._handle_slash_command("/unknown", history, "")
    assert handled is False
    assert model == ""
    out = capsys.readouterr().out
    assert "Unknown command" in out


def test_handle_slash_command_clear(tmp_path, monkeypatch, capsys):
    history = [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}]
    handled, model = interactive._handle_slash_command("/clear", history, "")
    assert handled is True
    assert model == ""
    assert history == []
    out = capsys.readouterr().out
    assert "Context cleared" in out


def test_handle_slash_command_history(tmp_path, monkeypatch, capsys):
    history = [
        {"role": "user", "content": "question"},
        {"role": "assistant", "content": "answer"},
    ]
    handled, model = interactive._handle_slash_command("/history", history, "")
    assert handled is True
    assert model == ""
    out = capsys.readouterr().out
    assert "question" in out
    assert "answer" in out


def test_handle_slash_command_model_show(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DEV_AI_MODEL", "gpt-4o")
    handled, model = interactive._handle_slash_command(
        "/model", history=[], session_model=""
    )
    assert handled is True
    assert model == ""
    out = capsys.readouterr().out
    assert "Current model" in out


def test_handle_slash_command_model_switch(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(interactive.Confirm, "ask", lambda *a, **k: True)
    handled, model = interactive._handle_slash_command(
        "/model claude-3", history=[], session_model=""
    )
    assert handled is True
    assert model == "claude-3"
    out = capsys.readouterr().out
    assert "Model switched to claude-3" in out


def test_handle_slash_command_model_keep(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(interactive.Confirm, "ask", lambda *a, **k: False)
    handled, model = interactive._handle_slash_command(
        "/model claude-3", history=[], session_model="gpt-4o"
    )
    assert handled is True
    assert model == "gpt-4o"
    out = capsys.readouterr().out
    assert "Model unchanged" in out


def test_handle_model_command_no_arg_shows_default(monkeypatch, capsys):
    monkeypatch.delenv("DEV_AI_MODEL", raising=False)
    result = interactive._handle_model_command("", current="")
    assert result == ""
    out = capsys.readouterr().out
    assert "Current model" in out


def test_handle_model_command_with_arg_confirms(monkeypatch, capsys):
    monkeypatch.setattr(interactive.Confirm, "ask", lambda *a, **k: True)
    result = interactive._handle_model_command("claude-3", current="gpt-4o")
    assert result == "claude-3"
    out = capsys.readouterr().out
    assert "Model switched" in out


def test_handle_model_command_with_arg_declines(monkeypatch, capsys):
    monkeypatch.setattr(interactive.Confirm, "ask", lambda *a, **k: False)
    result = interactive._handle_model_command("claude-3", current="gpt-4o")
    assert result == "gpt-4o"
    out = capsys.readouterr().out
    assert "Model unchanged" in out
