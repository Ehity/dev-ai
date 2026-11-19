"""Unit tests for the standup command (dev_ai.commands.standup)."""

from dev_ai.commands import standup


def test_since_default():
    """SINCE default is '1 day ago'."""
    assert standup.SINCE == "1 day ago"


def test_git_config_returns_value(monkeypatch):
    """_git_config returns the configured value."""
    calls = []

    def fake_run(cmd, capture_output, text, check):
        calls.append(cmd)
        class R:
            returncode = 0
            stdout = "John Doe\n"
            stderr = ""
        return R()

    monkeypatch.setattr(standup.subprocess, "run", fake_run)
    assert standup._git_config("user.name") == "John Doe"


def test_git_config_returns_empty_when_not_set(monkeypatch):
    """_git_config returns '' when the key is not configured."""
    def fake_run(cmd, capture_output, text, check):
        class R:
            returncode = 1
            stdout = ""
            stderr = ""
        return R()

    monkeypatch.setattr(standup.subprocess, "run", fake_run)
    assert standup._git_config("user.name") == ""


def test_git_config_returns_empty_when_git_missing(monkeypatch):
    """_git_config returns '' when git is not installed."""
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(standup.subprocess, "run", fake_run)
    assert standup._git_config("user.name") == ""


def test_get_recent_commits_not_git_repo(monkeypatch):
    """Empty list when not in a git repository."""
    monkeypatch.setattr(standup, "is_git_repository", lambda: False)
    monkeypatch.setattr(standup.console, "print", lambda *a, **k: None)
    assert standup.get_recent_commits() == []


def test_get_recent_commits_git_missing(monkeypatch):
    """Empty list when git is not installed."""
    monkeypatch.setattr(standup, "is_git_repository", lambda: True)
    monkeypatch.setattr(standup.console, "print", lambda *a, **k: None)

    def fake_run(*args, **kwargs):
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(standup.subprocess, "run", fake_run)
    assert standup.get_recent_commits() == []


def test_get_recent_commits_with_author(monkeypatch):
    """Commits are filtered by the configured git user.name."""
    monkeypatch.setattr(standup, "is_git_repository", lambda: True)
    monkeypatch.setattr(standup.console, "print", lambda *a, **k: None)
    monkeypatch.setattr(standup, "_git_config", lambda name: "Alice")

    calls = []

    def fake_run(args, capture_output, text, check):
        calls.append(args)
        class R:
            returncode = 0
            stdout = "Fix bug\nAdd feature\n"
            stderr = ""
        return R()

    monkeypatch.setattr(standup.subprocess, "run", fake_run)
    result = standup.get_recent_commits()
    assert result == ["Fix bug", "Add feature"]
    assert any("--author=Alice" in a for a in calls)


def test_get_recent_commits_no_author(monkeypatch):
    """All commits are shown when user.name is not set."""
    monkeypatch.setattr(standup, "is_git_repository", lambda: True)
    monkeypatch.setattr(standup.console, "print", lambda *a, **k: None)
    monkeypatch.setattr(standup, "_git_config", lambda name: "")

    def fake_run(args, capture_output, text, check):
        class R:
            returncode = 0
            stdout = "Update docs\n"
            stderr = ""
        return R()

    monkeypatch.setattr(standup.subprocess, "run", fake_run)
    result = standup.get_recent_commits()
    assert result == ["Update docs"]


def test_get_recent_commits_git_failure(monkeypatch):
    """Empty list when git log fails."""
    monkeypatch.setattr(standup, "is_git_repository", lambda: True)
    monkeypatch.setattr(standup.console, "print", lambda *a, **k: None)

    def fake_run(args, capture_output, text, check):
        class R:
            returncode = 128
            stdout = ""
            stderr = "fatal: bad revision"
        return R()

    monkeypatch.setattr(standup.subprocess, "run", fake_run)
    assert standup.get_recent_commits() == []


def test_standup_no_commits(monkeypatch):
    """Empty string when there are no commits."""
    monkeypatch.setattr(standup, "get_recent_commits", lambda: [])
    monkeypatch.setattr(standup.console, "print", lambda *a, **k: None)
    assert standup.standup() == ""


def test_standup_calls_llm_and_returns(monkeypatch):
    """standup sends commits to LLM and returns the report."""
    commits = ["Fix bug", "Add feature"]
    monkeypatch.setattr(standup, "get_recent_commits", lambda: commits)
    monkeypatch.setattr(standup.console, "print", lambda *a, **k: None)

    calls = []

    def fake_ask_llm(prompt):
        calls.append(prompt)
        return "## Done\n- Fixed a bug\n"

    monkeypatch.setattr(standup, "ask_llm", fake_ask_llm)
    result = standup.standup()
    assert len(calls) == 1
    assert "Fix bug" in calls[0]
    assert "Add feature" in calls[0]
    assert result == "## Done\n- Fixed a bug"


def test_standup_llm_error(monkeypatch, capsys):
    """Empty string when LLM returns an error."""
    monkeypatch.setattr(standup, "get_recent_commits", lambda: ["Fix bug"])
    monkeypatch.setattr(standup.console, "print", lambda *a, **k: None)
    monkeypatch.setattr(standup, "ask_llm", lambda prompt: "[api error] boom")
    assert standup.standup() == ""
