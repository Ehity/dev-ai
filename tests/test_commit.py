"""Unit tests for the commit command (dev_ai.commands.commit)."""

from dev_ai.commands import commit


def test_get_staged_diff_not_git_repo(monkeypatch, capsys):
    """Empty diff when not in a git repo."""
    monkeypatch.setattr(commit, "is_git_repository", lambda: False)
    result = commit.get_staged_diff()
    assert result == ""
    out = capsys.readouterr().out
    assert "not a git repository" in out


def test_get_staged_diff_empty(monkeypatch):
    """Empty string when nothing is staged."""
    monkeypatch.setattr(commit, "is_git_repository", lambda: True)
    monkeypatch.setattr(commit, "run_git_diff", lambda args: "")
    monkeypatch.setattr(commit.console, "print", lambda *a, **k: None)
    result = commit.get_staged_diff(quiet=True)
    assert result == ""


def test_get_staged_diff_with_content(monkeypatch):
    """Returns diff text when changes are staged."""
    monkeypatch.setattr(commit, "is_git_repository", lambda: True)
    monkeypatch.setattr(
        commit, "run_git_diff", lambda args: "diff --git a/foo.py b/foo.py"
    )
    monkeypatch.setattr(commit.console, "print", lambda *a, **k: None)
    result = commit.get_staged_diff(quiet=True)
    assert "diff --git" in result


def test_get_unstaged_diff_not_git_repo(monkeypatch, capsys):
    """Empty diff when not in a git repo."""
    monkeypatch.setattr(commit, "is_git_repository", lambda: False)
    result = commit.get_unstaged_diff()
    assert result == ""
    out = capsys.readouterr().out
    assert "not a git repository" in out


def test_get_unstaged_diff_with_content(monkeypatch):
    """Returns diff text when changes are unstaged."""
    monkeypatch.setattr(commit, "is_git_repository", lambda: True)
    monkeypatch.setattr(
        commit, "run_git_diff", lambda args: "diff --git a/bar.py b/bar.py"
    )
    monkeypatch.setattr(commit.console, "print", lambda *a, **k: None)
    result = commit.get_unstaged_diff(quiet=True)
    assert "diff --git" in result


def test_generate_commit_message_nothing_staged(monkeypatch):
    """Empty string when nothing staged."""
    monkeypatch.setattr(commit, "get_staged_diff", lambda: "")
    monkeypatch.setattr(commit.console, "print", lambda *a, **k: None)
    result = commit.generate_commit_message()
    assert result == ""


def test_generate_commit_message_calls_llm(monkeypatch):
    """Calls LLM with system prompt + diff and returns stripped message."""
    monkeypatch.setattr(commit, "get_staged_diff", lambda: "diff content")
    calls = []

    def fake_ask_llm(prompt):
        calls.append(prompt)
        return "feat: add something"

    monkeypatch.setattr(commit, "ask_llm", fake_ask_llm)
    monkeypatch.setattr(commit.console, "print", lambda *a, **k: None)
    result = commit.generate_commit_message()
    assert len(calls) == 1
    assert "diff content" in calls[0]
    assert result == "feat: add something"


def test_generate_commit_message_error(monkeypatch):
    """Empty string when LLM returns an error."""
    monkeypatch.setattr(commit, "get_staged_diff", lambda: "diff content")
    monkeypatch.setattr(commit, "ask_llm", lambda prompt: "[api error] boom")
    monkeypatch.setattr(commit.console, "print", lambda *a, **k: None)
    result = commit.generate_commit_message()
    assert result == ""


def test_run_git_commit_success(monkeypatch, capsys):
    """Returns True and prints success on successful git commit."""
    class FakeResult:
        returncode = 0
        stdout = "commit abc123\n"
        stderr = ""

    def fake_run(cmd, capture_output, text, check):
        return FakeResult()

    monkeypatch.setattr(commit.subprocess, "run", fake_run)
    monkeypatch.setattr(commit.console, "print", lambda *a, **k: None)
    assert commit.run_git_commit("feat: test") is True


def test_run_git_commit_failure(monkeypatch, capsys):
    """Returns False when git commit fails."""
    class FakeResult:
        returncode = 1
        stdout = ""
        stderr = "nothing to commit"

    def fake_run(cmd, capture_output, text, check):
        return FakeResult()

    monkeypatch.setattr(commit.subprocess, "run", fake_run)
    monkeypatch.setattr(commit.console, "print", lambda *a, **k: None)
    assert commit.run_git_commit("feat: test") is False


def test_run_git_commit_no_git(monkeypatch, capsys):
    """Returns False when git is not installed."""
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(commit.subprocess, "run", fake_run)
    assert commit.run_git_commit("feat: test") is False
    out = capsys.readouterr().out
    assert "not installed" in out


def test_commit_cancelled(monkeypatch):
    """Returns 0 when user cancels the commit."""
    monkeypatch.setattr(commit, "generate_commit_message", lambda: "feat: test")
    monkeypatch.setattr(commit.Confirm, "ask", lambda *a, **k: False)
    monkeypatch.setattr(commit.console, "print", lambda *a, **k: None)
    assert commit.commit() == 0


def test_commit_success(monkeypatch):
    """Returns 0 when commit succeeds."""
    monkeypatch.setattr(commit, "generate_commit_message", lambda: "feat: test")
    monkeypatch.setattr(commit.Confirm, "ask", lambda *a, **k: True)
    monkeypatch.setattr(commit, "run_git_commit", lambda msg: True)
    monkeypatch.setattr(commit.console, "print", lambda *a, **k: None)
    assert commit.commit() == 0


def test_commit_failure(monkeypatch):
    """Returns 1 when git commit fails."""
    monkeypatch.setattr(commit, "generate_commit_message", lambda: "feat: test")
    monkeypatch.setattr(commit.Confirm, "ask", lambda *a, **k: True)
    monkeypatch.setattr(commit, "run_git_commit", lambda msg: False)
    monkeypatch.setattr(commit.console, "print", lambda *a, **k: None)
    assert commit.commit() == 1
