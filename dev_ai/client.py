"""LLM API client for dev-ai.

Sends prompts to an OpenAI-compatible chat completions endpoint
(OpenAI or OpenRouter) using settings from dev_ai.config.
"""

import time
from typing import Any, Optional

import httpx

from dev_ai import config
from dev_ai.services import usage_tracker

REQUEST_TIMEOUT = 60.0


def ask_llm(
    prompt: str,
    model: str = "",
    language: str = "",
    history: Optional[list] = None,
    command: str = "ask_llm",
) -> str:
    """Send a prompt to the LLM chat completions API and return the reply.

    Args:
        prompt: User prompt text.
        model: Model name (e.g. "gpt-4o-mini"). When empty, the model
            from DEV_AI_MODEL (or the built-in default) is used.
        language: ISO code of the answer language (e.g. "ru"). When
            empty, the DEV_AI_LANG setting is used.
        history: Optional list of previous chat messages, each a dict
            with "role" ("user" or "assistant") and "content". The
            history is sent before the current prompt, so multi-turn
            conversations keep their context.
        command: The CLI command that issued this request; recorded in
            the usage tracker (e.g. "ask", "commit", "review").

    Returns:
        The assistant reply text, or an error message describing
        what went wrong (missing key, network failure, API error).
    """
    # 1. Validate configuration before doing any network work.
    try:
        api_key = config.get_api_key()
    except RuntimeError as exc:
        return f"[config error] {exc}"

    model = model.strip() or config.get_model()
    language = language.strip() or config.get_language()

    base_url = config.get_base_url().rstrip("/")
    url = f"{base_url}/chat/completions"

    messages: list[dict[str, Any]] = []
    # Ask for the configured answer language explicitly; the default
    # "en" needs no extra instruction.
    if language and language.lower() not in {"en", "english"}:
        messages.append(
            {"role": "system", "content": f"Answer in {language}."}
        )
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 2. Perform the request and turn every failure mode into a
    #    friendly message instead of an unhandled exception.
    started = time.monotonic()
    try:
        response = httpx.post(
            url,
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.TimeoutException:
        _track("timeout", model, started, command)
        return f"[network error] Request to {url} timed out ({REQUEST_TIMEOUT}s)."
    except httpx.ConnectError as exc:
        _track("connect_error", model, started, command)
        return f"[network error] Could not connect to {base_url}: {exc}"
    except httpx.HTTPStatusError as exc:
        _track(f"http_{exc.response.status_code}", model, started, command)
        status = exc.response.status_code
        detail = _extract_api_error(exc.response)
        if status == 401:
            return (
                "[api error] Authentication failed (401). "
                f"Check your OPENAI_API_KEY. Details: {detail}"
            )
        return f"[api error] HTTP {status}: {detail}"
    except httpx.HTTPError as exc:
        _track("network_error", model, started, command)
        return f"[network error] Request failed: {exc}"

    # 3. Parse the response body and record token usage.
    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        _track("bad_response", model, started, command)
        return f"[api error] Unexpected response format: {response.text[:300]}"

    _track_usage(data, model, started, command)
    return content


def _track(
    status: str, model: str, started: float, command: str = "ask_llm"
) -> None:
    """Record a failed request (no token counts available)."""
    duration_ms = int((time.monotonic() - started) * 1000)
    usage_tracker.record_request(
        command=command,
        model=model,
        duration_ms=duration_ms,
        status=status,
    )


def _track_usage(
    data: dict, model: str, started: float, command: str = "ask_llm"
) -> None:
    """Record a successful request with token counts from the API."""
    duration_ms = int((time.monotonic() - started) * 1000)
    usage = data.get("usage") or {}
    usage_tracker.record_request(
        command=command,
        model=model,
        input_tokens=int(usage.get("prompt_tokens", 0) or 0),
        output_tokens=int(usage.get("completion_tokens", 0) or 0),
        duration_ms=duration_ms,
        status="ok",
    )


def _extract_api_error(response: httpx.Response) -> str:
    """Best-effort extraction of an error message from an API response."""
    try:
        data = response.json()
        error = data.get("error", {})
        if isinstance(error, dict):
            return str(error.get("message", response.text[:300]))
        return str(error)
    except ValueError:
        return response.text[:300]
