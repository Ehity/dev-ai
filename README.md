# dev-ai

[![CI](https://github.com/Ehity/dev-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/Ehity/dev-ai/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

AI-powered CLI assistant for developers.

## Overview

`dev-ai` brings AI assistance straight into the terminal. It wraps common
developer chores—writing commit messages, reviewing code, generating tests
and docstrings, explaining errors—behind a simple set of commands backed by
an OpenAI-compatible LLM.

## Commands

| Command | Description |
|---|---|
| `dev-ai hello` | Greet the user (quick smoke test) |
| `dev-ai commit` | Generate a Conventional Commits message from staged changes and commit |
| `dev-ai review` | Review a file or the current git diff |
| `dev-ai doc` | Generate Google-style docstrings for a Python file |
| `dev-ai test` | Generate pytest tests for a Python module |
| `dev-ai ask` | Ask the LLM any question (also works via stdin pipe) |
| `dev-ai explain` | Explain an error, log or stack trace |
| `dev-ai refactor` | Refactor a Python file with readability improvements |
| `dev-ai standup` | Generate a Daily Standup from recent git commits |
| `dev-ai config` | Show or update model, language and API settings |
| `dev-ai interactive` | Continuous REPL chat (alias: `shell`) |
| `dev-ai template add\|list\|run\|remove` | Manage reusable prompt templates |
| `dev-ai export history` | Export session history to MD/JSON/TXT |
| `dev-ai stats` | Token usage statistics (`--today`, `--model`) |

## Interactive REPL

```bash
dev-ai interactive
```

Inside the REPL, use slash commands:

| Command | Action |
|---|---|
| `/help` | Show the slash-command reference |
| `/clear` | Clear the screen and reset context |
| `/history` | Show the conversation so far |
| `/model <name>` | Switch the LLM model for this session |
| `exit`, `quit`, `q` | Exit (also Ctrl+C / Ctrl+D) |

The REPL persists the session to `dev-ai_session.txt` and offers to
resume it on the next run. Piped input also works:

```bash
cat error.log | dev-ai explain
git diff | dev-ai ask "summarise these changes"
```

## Usage statistics

Every LLM request is recorded (model, token counts, duration) in
`~/.dev_ai/usage.json`. Inspect it any time:

```bash
dev-ai stats --today            # today's requests
dev-ai stats --model gpt-4o     # filter by model
```

## Configuration

Copy `.env.example` to `.env` and fill in your API key:

```bash
cp .env.example .env
```

Supported variables:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | API key (OpenAI or OpenRouter) |
| `API_BASE_URL` | Override for OpenRouter or a local proxy |
| `DEV_AI_MODEL` | Default LLM model (e.g. `gpt-4o-mini`) |
| `DEV_AI_LANG` | Response language (e.g. `ru`) |

## Installation

```bash
pip install -e .
dev-ai --help
```

## Development

```bash
ruff check dev_ai            # lint
python -m compileall dev_ai  # compile
python -m pytest -q          # tests (CI runs these on every push)
```

## License

MIT
