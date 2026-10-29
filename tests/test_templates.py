"""Unit tests for the template command (dev_ai.commands.templates)."""

import pytest
import typer

from dev_ai.commands import templates


def test_load_templates_missing_file(tmp_path, monkeypatch):
    templates.TEMPLATES_FILE = tmp_path / "templates.json"
    assert templates._load_templates() == {}


def test_load_templates_broken_json(tmp_path, monkeypatch):
    templates.TEMPLATES_FILE = tmp_path / "templates.json"
    templates.TEMPLATES_FILE.write_text("{not valid json", encoding="utf-8")
    assert templates._load_templates() == {}


def test_load_templates_non_dict(tmp_path, monkeypatch):
    templates.TEMPLATES_FILE = tmp_path / "templates.json"
    templates.TEMPLATES_FILE.write_text('["a", "b"]', encoding="utf-8")
    assert templates._load_templates() == {}


def test_load_templates_valid(tmp_path, monkeypatch):
    templates.TEMPLATES_FILE = tmp_path / "templates.json"
    templates.TEMPLATES_FILE.write_text(
        '{"greet": "Say hello", "review": "Review this code"}',
        encoding="utf-8",
    )
    assert templates._load_templates() == {
        "greet": "Say hello",
        "review": "Review this code",
    }


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    templates.TEMPLATES_FILE = tmp_path / "templates.json"
    templates._save_templates({"a": "1", "b": "2"})
    assert templates._load_templates() == {"a": "1", "b": "2"}


def test_add_template_saves_and_prints(tmp_path, monkeypatch, capsys):
    templates.TEMPLATES_FILE = tmp_path / "templates.json"
    templates.add_template("greet", "Say hello")
    assert templates._load_templates() == {"greet": "Say hello"}
    out = capsys.readouterr().out
    assert "Saved template" in out
    assert "greet" in out


def test_add_template_updates_existing(tmp_path, monkeypatch, capsys):
    templates.TEMPLATES_FILE = tmp_path / "templates.json"
    templates.add_template("greet", "Say hello")
    templates.add_template("greet", "Hi there")
    assert templates._load_templates() == {"greet": "Hi there"}
    out = capsys.readouterr().out
    assert "Updated template" in out


def test_remove_template(tmp_path, monkeypatch, capsys):
    templates.TEMPLATES_FILE = tmp_path / "templates.json"
    templates._save_templates({"a": "1", "b": "2"})
    templates.remove_template("a")
    assert templates._load_templates() == {"b": "2"}
    out = capsys.readouterr().out
    assert "Removed template" in out


def test_remove_template_missing(tmp_path, monkeypatch, capsys):
    templates.TEMPLATES_FILE = tmp_path / "templates.json"
    templates.TEMPLATES_FILE.write_text("{}", encoding="utf-8")
    with pytest.raises(typer.Exit):
        templates.remove_template("nope")
    out = capsys.readouterr().out
    assert "template not found" in out


def test_list_templates_empty(tmp_path, monkeypatch, capsys):
    templates.TEMPLATES_FILE = tmp_path / "templates.json"
    templates.list_templates()
    out = capsys.readouterr().out
    assert "No templates saved yet" in out


def test_list_templates_non_empty(tmp_path, monkeypatch, capsys):
    templates.TEMPLATES_FILE = tmp_path / "templates.json"
    templates._save_templates({"zebra": "last", "alpha": "first"})
    templates.list_templates()
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "zebra" in out
    assert "first" in out
    assert "last" in out


def test_run_template_missing(tmp_path, monkeypatch, capsys):
    templates.TEMPLATES_FILE = tmp_path / "templates.json"
    templates.TEMPLATES_FILE.write_text("{}", encoding="utf-8")
    with pytest.raises(typer.Exit):
        templates.run_template("nope", None)
    out = capsys.readouterr().out
    assert "template not found" in out


def test_run_template_sends_to_llm(tmp_path, monkeypatch, capsys):
    templates.TEMPLATES_FILE = tmp_path / "templates.json"
    templates._save_templates({"greet": "Say hello"})

    calls = []
    rendered = []

    def fake_ask_llm(prompt: str) -> str:
        calls.append(prompt)
        return "LLM answer"

    def fake_print_markdown(text: str) -> None:
        rendered.append(text)

    monkeypatch.setattr(templates, "ask_llm", fake_ask_llm)
    monkeypatch.setattr(templates, "print_markdown", fake_print_markdown)

    templates.run_template("greet", None)
    assert calls == ["Say hello"]
    assert rendered == ["LLM answer"]
