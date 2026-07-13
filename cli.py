"""Command-line interface for the Amazon Bedrock POC.

Three subcommands, one per use case:

    python cli.py chat
    python cli.py summarize --file report.txt
    python cli.py ask --file report.txt --question "What is the deadline?"

Run ``python cli.py --help`` (or ``<subcommand> --help``) for full usage.

Design note: this file is intentionally the only "I/O" layer for the terminal — it
parses arguments, reads files, prints output, and maps errors to exit codes. All the
Bedrock logic lives in the ``bedrock_poc`` package so it can be reused by the web UI.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from bedrock_poc import client as bedrock
from bedrock_poc import use_cases

# Configure logging once, here at the entry point. INFO by default; flip to DEBUG with
# the --verbose flag. We keep the format short so it reads cleanly in a terminal.
log = logging.getLogger("bedrock_poc.cli")


def _read_document(file_path: str) -> str:
    """Read a UTF-8 text document from disk for the summarize/ask commands.

    Args:
        file_path: Path to a plain-text file.

    Returns:
        The file's contents as a string.

    Raises:
        SystemExit: With a clear message if the file is missing or unreadable — this is
            an operator error, so we exit rather than raise a traceback.
    """
    path = Path(file_path)
    try:
        # errors="replace" keeps the demo alive on files with odd bytes instead of
        # crashing on a decode error.
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        sys.exit(f"Error: file not found: {file_path}")
    except OSError as err:
        sys.exit(f"Error: could not read file '{file_path}': {err}")


def _run_chat(client) -> None:
    """Run an interactive, multi-turn chat loop in the terminal.

    Maintains the conversation history in memory for the life of the loop so the model
    has context across turns. Type 'exit' or 'quit' (or send EOF / Ctrl-D) to leave.

    Args:
        client: A ``bedrock-runtime`` client from :func:`bedrock.build_client`.
    """
    print("Bedrock chat — type 'exit' or 'quit' to leave.\n")

    # The running conversation, in Bedrock Converse shape. Grows by two entries (user +
    # assistant) each turn.
    history: list[dict] = []

    while True:
        try:
            user_message = input("you> ").strip()
        except EOFError:
            # Ctrl-D — treat as a clean exit.
            print()
            break

        if user_message.lower() in {"exit", "quit"}:
            break
        if not user_message:
            # Ignore blank input instead of sending an empty request.
            continue

        try:
            # Buffered reply keeps the CLI simple; the web UI uses streaming instead.
            reply = use_cases.chat_turn(client, history, user_message)
        except RuntimeError as err:
            # A single failed turn should not kill the session — report and continue.
            print(f"[error] {err}\n")
            continue

        print(f"bot> {reply}\n")

        # Persist both sides of the exchange so the next turn has full context.
        history.append({"role": "user", "content": [{"text": user_message}]})
        history.append({"role": "assistant", "content": [{"text": reply}]})


def _run_summarize(client, args: argparse.Namespace) -> None:
    """Summarize a document file and print the result.

    Args:
        client: A ``bedrock-runtime`` client.
        args: Parsed CLI arguments (expects ``args.file`` and ``args.max_tokens``).
    """
    document = _read_document(args.file)
    try:
        summary = use_cases.summarize_document(client, document, max_tokens=args.max_tokens)
    except (ValueError, RuntimeError) as err:
        sys.exit(f"Error: {err}")

    print(summary)


def _run_ask(client, args: argparse.Namespace) -> None:
    """Answer a question about a document file and print the answer.

    Args:
        client: A ``bedrock-runtime`` client.
        args: Parsed CLI arguments (expects ``args.file``, ``args.question``,
            ``args.max_tokens``).
    """
    document = _read_document(args.file)
    try:
        answer = use_cases.answer_question(
            client, document, args.question, max_tokens=args.max_tokens
        )
    except (ValueError, RuntimeError) as err:
        sys.exit(f"Error: {err}")

    print(answer)


def _build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser with one subcommand per use case.

    Returns:
        The configured top-level argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Amazon Bedrock POC — chat, document summarization, and Q&A.",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable DEBUG logging."
    )

    # ``required=True`` forces the user to pick a subcommand rather than doing nothing.
    subparsers = parser.add_subparsers(dest="command", required=True)

    # chat — no extra args; it drops into an interactive loop.
    subparsers.add_parser("chat", help="Start an interactive multi-turn chat.")

    # summarize --file [--max-tokens]
    p_sum = subparsers.add_parser("summarize", help="Summarize a text document.")
    p_sum.add_argument("--file", required=True, help="Path to a text file to summarize.")
    p_sum.add_argument(
        "--max-tokens", type=int, default=512, dest="max_tokens",
        help="Max tokens for the summary (default: 512).",
    )

    # ask --file --question [--max-tokens]
    p_ask = subparsers.add_parser("ask", help="Ask a question about a text document.")
    p_ask.add_argument("--file", required=True, help="Path to the source text file.")
    p_ask.add_argument("--question", required=True, help="The question to answer.")
    p_ask.add_argument(
        "--max-tokens", type=int, default=512, dest="max_tokens",
        help="Max tokens for the answer (default: 512).",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point: parse arguments, build the client, dispatch to the use case.

    Args:
        argv: Optional argument list (defaults to ``sys.argv``). Useful for testing.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Set up logging based on the verbosity flag before any Bedrock work happens.
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    # Build the client once; a bad AWS/region setup fails here with a clear message.
    try:
        client = bedrock.build_client()
    except RuntimeError as err:
        sys.exit(f"Error: {err}")

    log.info("Using Bedrock model: %s", bedrock.get_model_id())

    # Dispatch to the handler for the chosen subcommand.
    if args.command == "chat":
        _run_chat(client)
    elif args.command == "summarize":
        _run_summarize(client, args)
    elif args.command == "ask":
        _run_ask(client, args)


if __name__ == "__main__":
    main()
