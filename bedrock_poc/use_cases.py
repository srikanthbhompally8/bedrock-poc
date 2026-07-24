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

import json
import logging

from . import client as bedrock
from .models import ResumeParsed
from .vector_store import DocumentStore

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


# System prompt for resume parsing: precise extraction of structure.
RESUME_SYSTEM_PROMPT = (
    "You are an expert resume parser. Extract and structure the resume information "
    "into the provided JSON format. Be precise: extract only information explicitly "
    "stated in the resume. For lists (skills, experience, education), extract all entries. "
    "If a field is missing, use an empty string or empty list as appropriate."
)


def parse_resume(client, resume_text: str) -> ResumeParsed:
    """Parse a resume and extract structured information.

    Uses Claude to analyze a resume and extract key information into a structured
    format: name, email, skills, experience, education, etc.

    Args:
        client: A ``bedrock-runtime`` client from :func:`bedrock.build_client`.
        resume_text: The full text of the resume to parse.

    Returns:
        A ``ResumeParsed`` object with extracted resume information.

    Raises:
        ValueError: If ``resume_text`` is empty/whitespace.
        RuntimeError: If parsing fails or response is invalid JSON.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("Cannot parse an empty resume.")

    # Truncate resume if too long to avoid token limits
    max_resume_chars = 20000
    if len(resume_text) > max_resume_chars:
        log.warning("Resume is %d chars; truncating to %d", len(resume_text), max_resume_chars)
        resume_text = resume_text[:max_resume_chars]

    prompt = """Extract all information from this resume and return ONLY a valid JSON object with this exact structure:

{
  "full_name": "Person's full name (required)",
  "email": "Email address (required)",
  "phone": "Phone number or empty string",
  "summary": "Professional summary or empty string",
  "skills": ["skill1", "skill2", "skill3"],
  "experience": [
    {
      "company": "Company name",
      "title": "Job title",
      "dates": "Employment dates",
      "description": "Job description"
    }
  ],
  "education": [
    {
      "degree": "Degree type",
      "field": "Field of study",
      "school": "School name",
      "year": "Graduation year"
    }
  ]
}

Resume to parse:
---
""" + resume_text + "\n---\n\nReturn ONLY the JSON object, no other text."

    messages = [{"role": "user", "content": [{"text": prompt}]}]

    try:
        # Use low temperature for consistent, structured output
        response = bedrock.converse(
            client,
            messages,
            system_prompt=RESUME_SYSTEM_PROMPT,
            max_tokens=2000,
            temperature=0.1,
        )

        log.info("Received response from Bedrock: %s chars", len(response))

        if not response or not response.strip():
            raise RuntimeError("Bedrock returned an empty response. Check if the resume format is valid.")

        # Try to extract JSON from response (in case there's extra text)
        response_clean = response.strip()
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        if response_clean.startswith("```"):
            response_clean = response_clean[3:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()

        # Parse the JSON response
        parsed_json = json.loads(response_clean)
        result = ResumeParsed(**parsed_json)
        log.info("Successfully parsed resume: %s", result.full_name)
        return result

    except json.JSONDecodeError as err:
        raise RuntimeError(
            f"Failed to parse resume response as JSON: {err}\n"
            f"Response was: {response[:200]}..."
        )
    except ValueError as err:
        raise RuntimeError(f"Resume data validation failed: {err}")


def answer_question_with_rag(
    client, document_text: str, question: str, max_tokens: int = 512, top_k: int = 3
) -> str:
    """Answer a question using RAG (Retrieval-Augmented Generation).

    Chunks the document, embeds all chunks and the question, retrieves the most
    relevant chunks, and answers based on them. This handles large documents better
    than truncation by retrieving only the relevant parts.

    Args:
        client: A ``bedrock-runtime`` client from :func:`bedrock.build_client`.
        document_text: The source document to answer from.
        question: The user's question about the document.
        max_tokens: Upper bound on the answer length (in tokens).
        top_k: Number of document chunks to retrieve for context.

    Returns:
        The answer as plain text, grounded in the retrieved document chunks.

    Raises:
        ValueError: If the document or question is empty.
        RuntimeError: If embedding or retrieval fails.
    """
    # Validate inputs
    if not document_text or not document_text.strip():
        raise ValueError("Cannot answer a question without a document.")
    if not question or not question.strip():
        raise ValueError("Cannot answer an empty question.")

    log.info("Starting RAG for question: %s", question[:50])

    # Step 1: Chunk the document
    store = DocumentStore()
    num_chunks = store.add_documents(document_text, source="user_document")
    log.info("Created %d chunks from document", num_chunks)

    if num_chunks == 0:
        raise ValueError("Document is too small or empty after chunking.")

    # Step 2: Embed all document chunks
    chunks = store.get_all_chunks_for_embedding()
    try:
        log.info("Embedding %d document chunks…", len(chunks))
        chunk_embeddings = bedrock.embed_text(client, chunks)
        store.set_embeddings(chunk_embeddings)
    except RuntimeError as err:
        raise RuntimeError(f"Failed to embed document chunks: {err}") from err

    # Step 3: Embed the question
    try:
        question_embeddings = bedrock.embed_text(client, [question])
        question_embedding = question_embeddings[0]
    except RuntimeError as err:
        raise RuntimeError(f"Failed to embed question: {err}") from err

    # Step 4: Retrieve most relevant chunks
    relevant_docs = store.search(question_embedding, top_k=top_k)
    if not relevant_docs:
        log.warning("No relevant documents found for the question")
        return "No relevant information found in the document."

    # Step 5: Build context from retrieved chunks
    context = "\n---\n".join(doc.text for doc in relevant_docs)
    log.info("Retrieved %d relevant chunks for context", len(relevant_docs))

    # Step 6: Answer based on retrieved context
    prompt = (
        f"Context from document:\n\"\"\"\n{context}\n\"\"\"\n\n"
        f"Question: {question}"
    )
    messages = [{"role": "user", "content": [{"text": prompt}]}]

    try:
        answer = bedrock.converse(
            client,
            messages,
            system_prompt=QA_SYSTEM_PROMPT,
            max_tokens=max_tokens,
            temperature=0.1,
        )
        log.info("RAG answer generated successfully")
        return answer
    except RuntimeError as err:
        raise RuntimeError(f"Failed to generate answer: {err}") from err
