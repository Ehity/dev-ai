"""Environment configuration loader for dev-ai.

Reads API credentials and settings from a .env file located in the
project root (see .env.example for the list of supported variables).
"""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load .env from the project root. Variables already present in the
# real environment take precedence over values from the file.
load_dotenv(ENV_FILE)

DEFAULT_API_BASE_URL = "https://api.openai.com/v1"

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
API_BASE_URL: str = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).strip()

# Settings managed by the `dev-ai config` command. The DEV_AI_ prefix is
# used on purpose: a bare LANG would clash with the system locale
# variable on POSIX systems.
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_LANGUAGE = "en"

MODEL: str = os.getenv("DEV_AI_MODEL", "").strip() or DEFAULT_MODEL
LANGUAGE: str = os.getenv("DEV_AI_LANG", "").strip() or DEFAULT_LANGUAGE


def get_api_key() -> str:
    """Return the API key (OpenAI or OpenRouter) from the environment.

    Raises:
        RuntimeError: If OPENAI_API_KEY is not configured.
    """
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Copy .env.example to .env and add your API key."
        )
    return key


def get_base_url() -> str:
    """Return the API base URL (OpenAI by default, OpenRouter if set)."""
    return os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).strip()


def is_configured() -> bool:
    """Return True when an API key is available."""
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def get_model() -> str:
    """Return the LLM model name (DEV_AI_MODEL, or the default model)."""
    return os.getenv("DEV_AI_MODEL", "").strip() or DEFAULT_MODEL


def get_language() -> str:
    """Return the response language (DEV_AI_LANG, or the default one)."""
    return os.getenv("DEV_AI_LANG", "").strip() or DEFAULT_LANGUAGE


def set_env_value(key: str, value: str) -> None:
    """Persist a key=value pair in the .env file.

    Existing keys are updated in place so comments and unrelated
    settings are kept; unknown keys are appended. The variable is also
    exported to the current process so later reads see the new value.

    Args:
        key: Variable name (e.g. "DEV_AI_MODEL").
        value: Value to store.

    Raises:
        OSError: If the file cannot be read or written.
    """
    lines: List[str] = []
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()

    replacement = f"{key}={value}"
    replaced = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(key + "=") and not stripped.startswith("#"):
            lines[index] = replacement
            replaced = True
            break
    if not replaced:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(replacement)

    ENV_FILE.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
    os.environ[key] = value
