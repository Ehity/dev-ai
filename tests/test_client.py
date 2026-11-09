"""Unit tests for the LLM client (dev_ai.client)."""

from unittest.mock import MagicMock

from dev_ai import client


def test_ask_llm_returns_config_error_without_key(monkeypatch):
    """Missing OPENAI_API_KEY yields a [config error] message."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = client.ask_llm("Hello", command="test")
    assert "[config error]" in result


def test_ask_llm_uses_config_model(monkeypatch):
    """Empty model falls back to DEV_AI_MODEL / default."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("DEV_AI_MODEL", "gpt-4o-mini")

    calls = []

    def fake_post(url, json=None, headers=None, timeout=None):
        calls.append(json.get("model"))
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"choices": [{"message": {"content": "OK"}}]}
        return mock_resp

    monkeypatch.setattr(client.httpx, "post", fake_post)
    client.ask_llm("Hello", command="test")
    assert calls == ["gpt-4o-mini"]


def test_ask_llm_uses_explicit_model(monkeypatch):
    """Explicit model overrides the configured one."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("DEV_AI_MODEL", "gpt-4o-mini")

    calls = []

    def fake_post(url, json=None, headers=None, timeout=None):
        calls.append(json.get("model"))
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"choices": [{"message": {"content": "OK"}}]}
        return mock_resp

    monkeypatch.setattr(client.httpx, "post", fake_post)
    client.ask_llm("Hello", model="claude-3", command="test")
    assert calls == ["claude-3"]


def test_ask_llm_success_returns_content(monkeypatch):
    """Successful API call returns the assistant content."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    def fake_post(url, json=None, headers=None, timeout=None):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Hi there!"}}]
        }
        return mock_resp

    monkeypatch.setattr(client.httpx, "post", fake_post)
    assert client.ask_llm("Hello", command="test") == "Hi there!"


def test_ask_llm_timeout(monkeypatch):
    """Timeout yields a [network error] message."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    def fake_post(url, json=None, headers=None, timeout=None):
        raise client.httpx.TimeoutException("timed out")

    monkeypatch.setattr(client.httpx, "post", fake_post)
    result = client.ask_llm("Hello", command="test")
    assert "[network error]" in result


def test_extract_api_error_dict_message():
    """Nested error dict yields its message."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"error": {"message": "Internal server error"}}
    result = client._extract_api_error(mock_resp)
    assert "Internal server error" in result


def test_extract_api_error_string_error():
    """Plain string error is returned as-is."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"error": "Something went wrong"}
    result = client._extract_api_error(mock_resp)
    assert "Something went wrong" in result


def test_extract_api_error_no_json():
    """Unparseable JSON falls back to response text."""
    mock_resp = MagicMock()
    mock_resp.json.side_effect = ValueError("Bad JSON")
    mock_resp.text = "500 Server Error"
    result = client._extract_api_error(mock_resp)
    assert "500 Server Error" in result


def test_track_records_failed_request(monkeypatch, tmp_path):
    """Failed request metadata is written to the usage log."""
    import dev_ai.services.usage_tracker as ut

    ut.USAGE_FILE = tmp_path / "usage.json"

    client._track("timeout", "gpt-4o", 1000.0, command="test")
    records = ut.query()
    assert len(records) == 1
    r = records[0]
    assert r["command"] == "test"
    assert r["model"] == "gpt-4o"
    assert r["status"] == "timeout"
    assert r["in"] == 0
    assert r["out"] == 0


def test_track_usage_records_success(monkeypatch, tmp_path):
    """Successful request with tokens is written to the usage log."""
    import dev_ai.services.usage_tracker as ut

    ut.USAGE_FILE = tmp_path / "usage.json"

    data = {"usage": {"prompt_tokens": 50, "completion_tokens": 100}}
    client._track_usage(data, "gpt-4o", 1000.0, command="test")
    records = ut.query()
    assert len(records) == 1
    r = records[0]
    assert r["command"] == "test"
    assert r["model"] == "gpt-4o"
    assert r["in"] == 50
    assert r["out"] == 100
    assert r["status"] == "ok"
