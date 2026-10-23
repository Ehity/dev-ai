"""Unit tests for the usage tracker (dev_ai.services.usage_tracker)."""

import pytest

from dev_ai.services import usage_tracker


@pytest.fixture(autouse=True)
def isolated_usage_file(tmp_path, monkeypatch):
    """Point USAGE_FILE at a temp file for each test and reset state."""
    usage_tracker.USAGE_FILE = tmp_path / "usage.json"
    usage_tracker.reset()
    yield
    usage_tracker.reset()


def test_record_request_and_query(tmp_path):
    usage_tracker.record_request("ask", "gpt-4o", 100, 200, 1200, "ok")
    records = usage_tracker.query()
    assert len(records) == 1
    r = records[0]
    assert r["command"] == "ask"
    assert r["model"] == "gpt-4o"
    assert r["in"] == 100
    assert r["out"] == 200
    assert r["ms"] == 1200
    assert r["status"] == "ok"
    assert "ts" in r


def test_record_request_defaults():
    usage_tracker.record_request("commit", "gpt-4o-mini")
    records = usage_tracker.query()
    assert len(records) == 1
    r = records[0]
    assert r["in"] == 0
    assert r["out"] == 0
    assert r["ms"] == 0
    assert r["status"] == "ok"


def test_query_filters_by_today():
    usage_tracker.record_request("ask", "gpt-4o", 1, 1, 10, "ok")
    today = usage_tracker.query(today=True)
    assert len(today) == 1


def test_query_filters_by_model():
    usage_tracker.record_request("ask", "gpt-4o", 1, 1, 10, "ok")
    usage_tracker.record_request("doc", "gpt-3.5-turbo", 2, 2, 20, "ok")
    only_gpt4o = usage_tracker.query(model="gpt-4o")
    assert len(only_gpt4o) == 1
    assert only_gpt4o[0]["model"] == "gpt-4o"


def test_aggregate_sums_tokens_and_counts():
    usage_tracker.record_request("ask", "gpt-4o", 100, 200, 1000, "ok")
    usage_tracker.record_request("doc", "gpt-4o", 50, 75, 500, "ok")
    usage_tracker.record_request("review", "gpt-4o", 10, 10, 200, "http_error")
    summary = usage_tracker.aggregate(usage_tracker.query())
    assert summary["requests"] == 3
    assert summary["in"] == 160
    assert summary["out"] == 285
    assert summary["total"] == 445
    assert summary["errors"] == 1
    assert summary["avg_ms"] == int((1000 + 500 + 200) / 3)


def test_aggregate_empty_records():
    summary = usage_tracker.aggregate([])
    assert summary == {
        "requests": 0,
        "in": 0,
        "out": 0,
        "total": 0,
        "errors": 0,
        "avg_ms": 0,
    }


def test_reset_removes_file(tmp_path):
    usage_tracker.record_request("ask", "gpt-4o", 1, 1, 10, "ok")
    assert usage_tracker.USAGE_FILE.exists()
    usage_tracker.reset()
    assert not usage_tracker.USAGE_FILE.exists()


def test_now_ms_returns_positive_int():
    ms = usage_tracker.now_ms()
    assert isinstance(ms, int)
    assert ms > 0


def test_broken_usage_file_is_ignored(tmp_path):
    usage_tracker.USAGE_FILE.write_text("{not valid json", encoding="utf-8")
    assert usage_tracker.query() == []


def test_non_list_usage_file_is_ignored(tmp_path):
    usage_tracker.USAGE_FILE.write_text('"not a list"', encoding="utf-8")
    assert usage_tracker.query() == []


def test_record_request_never_raises(tmp_path, monkeypatch):
    """Even if saving fails, record_request must not break the CLI."""
    def fail(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(usage_tracker, "_save_records", fail)
    usage_tracker.record_request("ask", "gpt-4o", 1, 1, 10, "ok")
    # In-memory append still happens, but save fails — no exception propagates.


def test_max_records_pruned(tmp_path):
    usage_tracker.MAX_RECORDS = 3
    usage_tracker.record_request("a", "m1", 1, 1, 1, "ok")
    usage_tracker.record_request("b", "m1", 1, 1, 1, "ok")
    usage_tracker.record_request("c", "m1", 1, 1, 1, "ok")
    usage_tracker.record_request("d", "m1", 1, 1, 1, "ok")
    records = usage_tracker.query()
    assert len(records) == 3
    assert [r["command"] for r in records] == ["b", "c", "d"]
