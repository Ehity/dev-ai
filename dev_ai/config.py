"""Environment configuration loader for dev-ai.

Reads API credentials and settings from a .env file located in the
project root (see .env.example for the list of supported variables).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load .env from the project root. Variables already present in the
# real environment take precedence over values from the file.
load_dotenv(ENV_FILE)

DEFAULT_API_BASE_URL = "https://api.openai.com/v1"

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
API_BASE_URL: str = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).strip()


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
