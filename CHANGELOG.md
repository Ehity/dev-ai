# Changelog

All notable changes to **dev-ai** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `dev-ai stats` — token usage tracking (`--today`, `--model`) backed by
  `~/.dev_ai/usage.json`.
- `dev-ai export history` — export session history to MD/JSON/TXT.
- `dev-ai template add|list|run|remove` — reusable prompt templates.
- `CHANGELOG.md` documenting the release history.

### Changed
- CI now lints `dev_ai` and `tests` and runs `pytest` on every push.
- `pip install -e ".[dev]"` installs the extra test/lint dependencies.
- Unit tests for the shared helpers in `dev_ai/commands/_common.py`.

## [0.3.0] - 2026-10-18

### Added
- `dev-ai interactive` (alias `shell`) — REPL chat with session history and
  slash commands (`/help`, `/clear`, `/history`, `/model`).
- stdin pipe support for `ask` and `explain`
  (`cat error.log | dev-ai explain`).
- `dev-ai refactor` — readability-oriented refactoring with a change summary.
- `dev-ai standup` — Daily Standup generated from the last day of git commits.

### Changed
- Shared helpers extracted into `dev_ai/commands/_common.py` (DRY).
- `ask_llm` now accepts an optional conversation history.

## [0.2.0] - 2026-10-05

### Added
- `dev-ai config` — view and update model, language and API settings.
- `dev-ai explain` — error, log and stack-trace analysis.
- `dev-ai ask` — ask the LLM a question from the terminal.
- `dev-ai doc` — Google-style docstring generation with `--write` support.
- `dev-ai test` — pytest test generation with `tests/` auto-creation.

## [0.1.0] - 2026-09-30

### Added
- Initial project setup: `pyproject.toml`, packaging and the `dev-ai` entry point.
- `dev-ai hello` — greeting smoke test.
- `dev-ai commit` — Conventional Commits message generator.
- `dev-ai review` — code review for a file or the current git diff.
- Environment configuration loader (`dev_ai/config.py`) and `.env.example`.
- Basic LLM API client (`dev_ai/client.py`) with error handling.
- CI workflow: ruff lint, compileall and pytest on every push.
