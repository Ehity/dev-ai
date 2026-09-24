"""LLM API client for dev-ai.

Sends prompts to an OpenAI-compatible chat completions endpoint
(OpenAI or OpenRouter) using settings from dev_ai.config.
"""

from typing import Any

import httpx

from dev_ai import config

DEFAULT_MODEL = "gpt-4o-mini"
REQUEST_TIMEOUT = 60.0


def ask_llm(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Send a prompt to the LLM chat completions API and return the reply.

    Args:
        prompt: User prompt text.
        model: Model name (e.g. "gpt-4o-mini").

    Returns:
        The assistant reply text, or an error message describing
        what went wrong (missing key, network failure, API error).
    """
    # 1. Validate configuration before doing any network work.
    try:
        api_key = config.get_api_key()
    except RuntimeError as exc:
        return f"[config error] {exc}"

    base_url = config.get_base_url().rstrip("/")
    url = f"{base_url}/chat/completions"

    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 2. Perform the request and turn every failure mode into a
    #    friendly message instead of an unhandled exception.
    try:
        response = httpx.post(
            url,
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.TimeoutException:
        return f"[network error] Request to {url} timed out ({REQUEST_TIMEOUT}s)."
    except httpx.ConnectError as exc:
        return f"[network error] Could not connect to {base_url}: {exc}"
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        detail = _extract_api_error(exc.response)
        if status == 401:
            return (
                "[api error] Authentication failed (401). "
                f"Check your OPENAI_API_KEY. Details: {detail}"
            )
        return f"[api error] HTTP {status}: {detail}"
    except httpx.HTTPError as exc:
        return f"[network error] Request failed: {exc}"

    # 3. Parse the response body.
    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        return f"[api error] Unexpected response format: {response.text[:300]}"


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
