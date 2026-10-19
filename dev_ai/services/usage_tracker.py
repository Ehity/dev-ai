"""Usage tracker: persist LLM API call metadata to a local JSON file.

Every successful (and failed) call to ask_llm records one entry with the
timestamp, the command that triggered it, token counts returned by the
API and the response duration. Data is stored in ~/.dev_ai/usage.json so
it survives across sessions and is safe to share (no prompts or answers
are kept, only counters).
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Store under the user home directory: ~/.dev_ai/usage.json
USAGE_DIR = Path.home() / ".dev_ai"
USAGE_FILE = USAGE_DIR / "usage.json"

MAX_RECORDS = 5000


def _load_records() -> List[Dict[str, Any]]:
    """Read the usage log; missing or broken files yield an empty list."""
    try:
        data = json.loads(USAGE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    return data


def _save_records(records: List[Dict[str, Any]]) -> None:
    """Persist records, pruning the oldest entries above MAX_RECORDS."""
    USAGE_DIR.mkdir(parents=True, exist_ok=True)
    if len(records) > MAX_RECORDS:
        records = records[-MAX_RECORDS:]
    USAGE_FILE.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def record_request(
    command: str,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    duration_ms: int = 0,
    status: str = "ok",
) -> None:
    """Append one usage record to the log.

    Never raises: tracking must not break the CLI itself.

    Args:
        command: The CLI command that issued the request (e.g. "ask").
        model: The model name used for the request.
        input_tokens: Prompt tokens reported by the API (0 if unknown).
        output_tokens: Completion tokens reported by the API (0 if unknown).
        duration_ms: Request duration in milliseconds.
        status: "ok" or a short error label ("timeout", "http_error", ...).
    """
    try:
        record = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "command": command,
            "model": model,
            "in": int(input_tokens),
            "out": int(output_tokens),
            "ms": int(duration_ms),
            "status": status,
        }
        records = _load_records()
        records.append(record)
        _save_records(records)
    except Exception:  # noqa: BLE001 - tracking must never break the CLI
        pass


def query(
    today: bool = False,
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return usage records, optionally filtered.

    Args:
        today: Keep only records from the current local date.
        model: Keep only records for this exact model name.

    Returns:
        The matching records (list of dicts, may be empty).
    """
    records = _load_records()
    if today:
        day = datetime.now().date().isoformat()
        records = [r for r in records if str(r.get("ts", ""))[:10] == day]
    if model:
        records = [r for r in records if r.get("model") == model]
    return records


def aggregate(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute summary counters for a list of records.

    Returns:
        A dict with requests, in/out/total tokens, errors and the
        average response duration in milliseconds.
    """
    total_requests = len(records)
    in_tokens = sum(int(r.get("in", 0)) for r in records)
    out_tokens = sum(int(r.get("out", 0)) for r in records)
    errors = sum(1 for r in records if r.get("status") != "ok")
    durations = [int(r.get("ms", 0)) for r in records]
    avg_ms = int(sum(durations) / total_requests) if total_requests else 0
    return {
        "requests": total_requests,
        "in": in_tokens,
        "out": out_tokens,
        "total": in_tokens + out_tokens,
        "errors": errors,
        "avg_ms": avg_ms,
    }


def reset() -> None:
    """Delete the usage log (used by tests and by hand)."""
    try:
        if USAGE_FILE.exists():
            USAGE_FILE.unlink()
    except OSError:
        pass


def now_ms() -> int:
    """Return the current time in milliseconds (monotonic)."""
    return int(time.monotonic() * 1000)


__all__ = [
    "USAGE_FILE",
    "aggregate",
    "now_ms",
    "query",
    "record_request",
    "reset",
]
