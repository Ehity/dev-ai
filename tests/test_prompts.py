"""Unit tests for system prompts (dev_ai.prompts)."""

from dev_ai import prompts


def test_commit_prompt_contains_conventional_commits():
    assert "Conventional Commits" in prompts.COMMIT_SYSTEM_PROMPT
    assert "feat:" in prompts.COMMIT_SYSTEM_PROMPT
    assert "fix:" in prompts.COMMIT_SYSTEM_PROMPT


def test_code_review_prompt_contains_rules():
    assert "PEP 8" in prompts.CODE_REVIEW_SYSTEM_PROMPT
    assert "one-line overall verdict" in prompts.CODE_REVIEW_SYSTEM_PROMPT


def test_docstring_prompt_contains_google_style():
    assert "Google style" in prompts.DOCSTRING_SYSTEM_PROMPT
    assert "Args:" in prompts.DOCSTRING_SYSTEM_PROMPT


def test_unit_test_prompt_contains_pytest():
    assert "pytest" in prompts.UNIT_TEST_SYSTEM_PROMPT
    assert "test_" in prompts.UNIT_TEST_SYSTEM_PROMPT


def test_explain_prompt_contains_sections():
    assert "## What happened" in prompts.EXPLAIN_SYSTEM_PROMPT
    assert "## Root cause" in prompts.EXPLAIN_SYSTEM_PROMPT
    assert "## How to fix" in prompts.EXPLAIN_SYSTEM_PROMPT


def test_refactor_prompt_contains_improvements():
    assert "## Improvements" in prompts.REFACTOR_SYSTEM_PROMPT
    assert "PEP 8" in prompts.REFACTOR_SYSTEM_PROMPT


def test_standup_prompt_contains_sections():
    assert "## Done" in prompts.STANDUP_SYSTEM_PROMPT
    assert "## Next" in prompts.STANDUP_SYSTEM_PROMPT
    assert "## Blockers" in prompts.STANDUP_SYSTEM_PROMPT


def test_all_prompts_are_non_empty_strings():
    for name in [
        "COMMIT_SYSTEM_PROMPT",
        "CODE_REVIEW_SYSTEM_PROMPT",
        "DOCSTRING_SYSTEM_PROMPT",
        "UNIT_TEST_SYSTEM_PROMPT",
        "EXPLAIN_SYSTEM_PROMPT",
        "REFACTOR_SYSTEM_PROMPT",
        "STANDUP_SYSTEM_PROMPT",
    ]:
        value = getattr(prompts, name)
        assert isinstance(value, str)
        assert len(value) > 100, f"{name} is too short"
