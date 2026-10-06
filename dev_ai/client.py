"""LLM API client for dev-ai.

Sends prompts to an OpenAI-compatible chat completions endpoint
(OpenAI or OpenRouter) using settings from dev_ai.config.
"""

from typing import Any

import httpx

from dev_ai import config

REQUEST_TIMEOUT = 60.0


def ask_llm(
    prompt: str, model: str = "", language: str = ""
) -> str:
    """Send a prompt to the LLM chat completions API and return the reply.

    Args:
        prompt: User prompt text.
        model: Model name (e.g. "gpt-4o-mini"). When empty, the model
            from DEV_AI_MODEL (or the built-in default) is used.
        language: ISO code of the answer language (e.g. "ru"). When
            empty, the DEV_AI_LANG setting is used.

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

    messages: list[dict[str, Any]] = [
        {"role": "user", "content": prompt},
    ]
    # Ask for the configured answer language explicitly; the default
    # "en" needs no extra instruction.
    if language and language.lower() not in {"en", "english"}:
        messages.append(
            {"role": "system", "content": f"Answer in {language}."}
        )

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
