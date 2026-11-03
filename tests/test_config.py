"""Unit tests for the configuration loader (dev_ai.config)."""

import os

from dev_ai import config


def test_get_model_uses_default(monkeypatch):
    monkeypatch.delenv("DEV_AI_MODEL", raising=False)
    assert config.get_model() == config.DEFAULT_MODEL


def test_get_model_uses_env(monkeypatch):
    monkeypatch.setenv("DEV_AI_MODEL", "gpt-4o")
    assert config.get_model() == "gpt-4o"


def test_get_language_uses_default(monkeypatch):
    monkeypatch.delenv("DEV_AI_LANG", raising=False)
    assert config.get_language() == config.DEFAULT_LANGUAGE


def test_get_language_uses_env(monkeypatch):
    monkeypatch.setenv("DEV_AI_LANG", "ru")
    assert config.get_language() == "ru"


def test_get_base_url_default(monkeypatch):
    monkeypatch.delenv("API_BASE_URL", raising=False)
    assert config.get_base_url() == config.DEFAULT_API_BASE_URL


def test_get_base_url_custom(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "https://openrouter.ai/api/v1")
    assert config.get_base_url() == "https://openrouter.ai/api/v1"


def test_is_configured_false_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert config.is_configured() is False


def test_is_configured_true_with_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")
    assert config.is_configured() is True


def test_get_api_key_raises_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    try:
        config.get_api_key()
    except RuntimeError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:  # pragma: no cover - must raise
        raise AssertionError("get_api_key() must raise RuntimeError")


def test_get_api_key_returns_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret")
    assert config.get_api_key() == "sk-secret"


def test_set_env_value_writes_new_key(tmp_path, monkeypatch):
    config.ENV_FILE = tmp_path / ".env"
    config.set_env_value("DEV_AI_MODEL", "claude-3")
    text = config.ENV_FILE.read_text(encoding="utf-8")
    assert "DEV_AI_MODEL=claude-3" in text
    assert os.environ["DEV_AI_MODEL"] == "claude-3"


def test_set_env_value_updates_existing_key(tmp_path, monkeypatch):
    config.ENV_FILE = tmp_path / ".env"
    config.ENV_FILE.write_text("DEV_AI_MODEL=old\nOTHER=1\n", encoding="utf-8")
    config.set_env_value("DEV_AI_MODEL", "new-model")
    text = config.ENV_FILE.read_text(encoding="utf-8")
    assert "DEV_AI_MODEL=new-model" in text
    assert "OTHER=1" in text
    assert "old" not in text
