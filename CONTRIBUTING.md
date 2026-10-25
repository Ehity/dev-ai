# Contributing to dev-ai

Thanks for your interest in **dev-ai** — an AI-powered CLI assistant for developers.

## Ways to contribute

- Report bugs or request features via [GitHub Issues](https://github.com/Ehity/dev-ai/issues)
- Improve documentation (`README.md`, `CHANGELOG.md`, docstrings)
- Fix typos, lint warnings, or small bugs in `dev_ai/`
- Add unit tests in `tests/` for shared helpers and commands
- Suggest new CLI commands or REPL slash commands

## Getting started

```bash
git clone https://github.com/Ehity/dev-ai.git
cd dev-ai
pip install -e ".[dev]"
```

Run the checks before pushing:

```bash
ruff check dev_ai tests        # lint
python -m compileall -q dev_ai # compile
python -m pytest               # tests
```

## Pull requests

1. Create a branch from `main`: `git checkout -b my-change`
2. Make your changes and add tests when applicable
3. Run the checks above — all must pass
4. Commit with a conventional message, e.g. `feat: add ...` or `fix: ...`
5. Push to your branch and open a pull request against `main`

Commit style follows [Conventional Commits](https://www.conventionalcommits.org/):
`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`

## License

By contributing, you agree that your contributions will be licensed under the MIT License (see `LICENSE`).
