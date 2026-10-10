"""Ask command: query the LLM from an argument, a pipe, or both."""

from typing import Optional

from dev_ai.client import ask_llm
from dev_ai.commands._common import (
    console,
    looks_like_error,
    print_error,
    read_stdin,
)
from dev_ai.display import print_markdown

USAGE_HINT = (
    "nothing to ask; pass a question as an argument "
    "or pipe text via stdin (cat file.txt | dev-ai ask)"
)


def ask_question(question: Optional[str] = None) -> str:
    """Send a question to the LLM and print the answer as Markdown.

    The question is taken from the command line argument, from piped
    standard input (``cat file.txt | dev-ai ask``), or from both at
    once: when both are present they are joined into a single prompt.

    Args:
        question: The question passed as the CLI argument, if any.

    Returns:
        The answer text, or an empty string when there is no input or
        the request failed.
    """
    piped = read_stdin().strip()
    parts = [text for text in ((question or "").strip(), piped) if text]
    if not parts:
        print_error(USAGE_HINT)
        return ""

    prompt = "\n\n".join(parts)

    with console.status("[bold cyan]Thinking...[/bold cyan]"):
        message = ask_llm(prompt)

    if looks_like_error(message):
        print_error(message)
        return ""

    answer = message.strip()
    print_markdown(answer)
    return answer
