"""The three demo use cases, built on the Bedrock Converse wrapper in ``client.py``.

All three are the same underlying operation — send messages, get a reply — differing
only in the system prompt and how the input text is framed. Keeping them as small,
single-purpose functions makes each one easy to read, test, and reuse from either the
CLI or the web UI.

Use cases:
* :func:`chat_turn`        — one turn of a multi-turn conversation (keeps history).
* :func:`summarize_document` — condense a document into a short summary.
* :func:`answer_question`  — answer a question grounded in a supplied document.
"""

from __future__ import annotations

import logging

from . import client as bedrock

log = logging.getLogger(__name__)

# System prompt for free-form chat: friendly, concise, honest about uncertainty.
CHAT_SYSTEM_PROMPT = (
    "You are a helpful, concise assistant running on Amazon Bedrock. "
    "Answer clearly. If you are unsure, say so rather than guessing."
)

# System prompt for summarization: force tight, faithful summaries with no invention.
SUMMARY_SYSTEM_PROMPT = (
    "You are an expert summarizer. Produce a faithful, concise summary of the document "
    "the user provides. Preserve key facts, names, and numbers. Do not add information "
    "that is not present in the document."
)

# System prompt for document Q&A: answer ONLY from the document, admit gaps. This is the
# core guardrail that keeps answers grounded in the source instead of the model's priors.
QA_SYSTEM_PROMPT = (
    "You answer questions using ONLY the document provided by the user. "
    "If the answer is not contained in the document, reply exactly: "
    "'The document does not contain that information.' "
    "Quote or reference the relevant part of the document when helpful."
)

# Cap on how many characters of a document we send in a single request. This is a
# pragmatic guardrail for a POC — real production code would chunk large documents and
# retrieve the most relevant pieces (RAG) rather than truncating. We truncate (not
# reject) so the demo still works on an oversized file, and we log when it happens.
MAX_DOC_CHARS = 40_000


def _truncate_document(text: str) -> str:
    """Trim a document to :data:`MAX_DOC_CHARS`, logging if truncation occurred.

    Args:
        text: The full document text.

    Returns:
        The document, shortened to the character budget if it was over.
    """
    if len(text) <= MAX_DOC_CHARS:
        return text

    # Warn loudly: a truncated document can produce incomplete summaries/answers, and
    # the operator should know why.
    log.warning(
        "Document is %d chars; truncating to %d for this POC. "
        "Production use should chunk + retrieve instead of truncating.",
        len(text),
        MAX_DOC_CHARS,
    )
    return text[:MAX_DOC_CHARS]


def chat_turn(
    client,
    history: list[dict],
    user_message: str,
    stream: bool = False,
):
    """Run one turn of a multi-turn chat, returning the assistant's reply.

    The caller owns the conversation ``history`` list and is responsible for appending
    both the user message and the returned assistant reply to it before the next turn —
    that is how context is carried across turns.

    Args:
        client: A ``bedrock-runtime`` client from :func:`bedrock.build_client`.
        history: Prior turns in Bedrock Converse shape (may be empty for a new chat).
        user_message: The new user input for this turn.
        stream: If True, return a generator of text chunks (for a live-typing UI). If
            False, return the complete reply as a single string.

    Returns:
        A ``str`` when ``stream`` is False, or an ``Iterator[str]`` of chunks when True.
    """
    # Build the message list for this request: all prior turns plus the new user turn.
    # We do not mutate ``history`` here — the caller decides what to persist.
    messages = history + [{"role": "user", "content": [{"text": user_message}]}]

    if stream:
        # Streaming path — used by the web chat for the typewriter effect.
        return bedrock.converse_stream(
            client, messages, system_prompt=CHAT_SYSTEM_PROMPT, temperature=0.5
        )

    # Buffered path — used by the CLI. Slightly higher temperature than the doc use
    # cases because conversational replies benefit from a little variety.
    return bedrock.converse(
        client, messages, system_prompt=CHAT_SYSTEM_PROMPT, temperature=0.5
    )


def summarize_document(client, document_text: str, max_tokens: int = 512) -> str:
    """Summarize a document into a short, faithful summary.

    Args:
        client: A ``bedrock-runtime`` client from :func:`bedrock.build_client`.
        document_text: The full text of the document to summarize.
        max_tokens: Upper bound on the summary length (in tokens).

    Returns:
        The summary as plain text.

    Raises:
        ValueError: If ``document_text`` is empty/whitespace — there is nothing to do.
    """
    # Fail fast on empty input rather than paying for a pointless model call.
    if not document_text or not document_text.strip():
        raise ValueError("Cannot summarize an empty document.")

    document = _truncate_document(document_text)

    # Frame the document as a single user turn. A low temperature keeps the summary
    # faithful and repeatable rather than creative.
    messages = [
        {"role": "user", "content": [{"text": f"Summarize this document:\n\n{document}"}]}
    ]
    return bedrock.converse(
        client,
        messages,
        system_prompt=SUMMARY_SYSTEM_PROMPT,
        max_tokens=max_tokens,
        temperature=0.2,
    )


def answer_question(
    client, document_text: str, question: str, max_tokens: int = 512
) -> str:
    """Answer a question grounded strictly in the supplied document.

    This is the "RAG-lite" use case: the whole document is placed in context and the
    system prompt constrains the model to answer only from it. For large corpora,
    production code would retrieve the most relevant chunks instead of sending
    everything — but for a POC, in-context grounding shows the pattern clearly.

    Args:
        client: A ``bedrock-runtime`` client from :func:`bedrock.build_client`.
        document_text: The source document the answer must come from.
        question: The user's question about the document.
        max_tokens: Upper bound on the answer length (in tokens).

    Returns:
        The answer as plain text, or a fixed "not in the document" message when the
        document does not contain the answer (enforced by the system prompt).

    Raises:
        ValueError: If the document or the question is empty/whitespace.
    """
    # Both inputs are required — validate before spending a model call.
    if not document_text or not document_text.strip():
        raise ValueError("Cannot answer a question without a document.")
    if not question or not question.strip():
        raise ValueError("Cannot answer an empty question.")

    document = _truncate_document(document_text)

    # Clearly delimit the document from the question so the model does not confuse the
    # two. A very low temperature keeps answers grounded and consistent.
    prompt = (
        f"Document:\n\"\"\"\n{document}\n\"\"\"\n\n"
        f"Question: {question}"
    )
    messages = [{"role": "user", "content": [{"text": prompt}]}]
    return bedrock.converse(
        client,
        messages,
        system_prompt=QA_SYSTEM_PROMPT,
        max_tokens=max_tokens,
        temperature=0.1,
    )
