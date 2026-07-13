"""Smoke tests for the Bedrock POC that run WITHOUT any AWS calls.

These verify the request-shaping and control flow of the use cases by injecting a fake
Bedrock client. That means the suite runs offline, in CI, and for anyone without AWS
credentials — the real Bedrock call is exercised manually via the CLI/web UI.

Run from the ``bedrock-poc`` directory:

    python -m pytest tests/ -v
"""

from __future__ import annotations

import pytest

from bedrock_poc import use_cases


class FakeBedrockClient:
    """Stand-in for a boto3 bedrock-runtime client.

    Records the last ``converse`` request so tests can assert on what would have been
    sent, and returns a canned reply in the real Converse response envelope shape.
    """

    def __init__(self, reply_text: str = "canned reply"):
        # The text the fake will "generate".
        self.reply_text = reply_text
        # Captured kwargs from the most recent converse() call, for assertions.
        self.last_request: dict | None = None

    def converse(self, **kwargs):
        """Mimic client.converse: capture the request, return a canned response."""
        self.last_request = kwargs
        return {"output": {"message": {"content": [{"text": self.reply_text}]}}}


def test_summarize_builds_request_and_returns_text():
    """summarize_document should send the doc with the summary system prompt."""
    fake = FakeBedrockClient(reply_text="A short summary.")
    result = use_cases.summarize_document(fake, "Some document text.")

    # The reply is returned verbatim (trimmed).
    assert result == "A short summary."
    # The summary system prompt was applied.
    assert fake.last_request["system"][0]["text"] == use_cases.SUMMARY_SYSTEM_PROMPT
    # The document text made it into the user message.
    assert "Some document text." in fake.last_request["messages"][0]["content"][0]["text"]


def test_summarize_rejects_empty_document():
    """An empty document should raise ValueError before any client call."""
    fake = FakeBedrockClient()
    with pytest.raises(ValueError):
        use_cases.summarize_document(fake, "   ")
    # No request should have been attempted.
    assert fake.last_request is None


def test_answer_question_grounds_on_document():
    """answer_question should include both the document and the question."""
    fake = FakeBedrockClient(reply_text="42")
    result = use_cases.answer_question(fake, "The answer is 42.", "What is the answer?")

    assert result == "42"
    sent = fake.last_request["messages"][0]["content"][0]["text"]
    assert "The answer is 42." in sent
    assert "What is the answer?" in sent
    # The grounding guardrail prompt was applied.
    assert fake.last_request["system"][0]["text"] == use_cases.QA_SYSTEM_PROMPT


def test_answer_question_requires_question():
    """A blank question should raise ValueError."""
    fake = FakeBedrockClient()
    with pytest.raises(ValueError):
        use_cases.answer_question(fake, "some doc", "")


def test_chat_turn_appends_new_user_message():
    """chat_turn should send prior history plus the new user turn, in order."""
    fake = FakeBedrockClient(reply_text="hi there")
    history = [
        {"role": "user", "content": [{"text": "hello"}]},
        {"role": "assistant", "content": [{"text": "hey"}]},
    ]
    result = use_cases.chat_turn(fake, history, "how are you?")

    assert result == "hi there"
    sent_messages = fake.last_request["messages"]
    # Original two turns preserved, new user turn appended last.
    assert len(sent_messages) == 3
    assert sent_messages[-1]["content"][0]["text"] == "how are you?"
    # chat_turn must not mutate the caller's history list.
    assert len(history) == 2


def test_long_document_is_truncated(caplog):
    """Documents over the char budget should be truncated (and logged)."""
    fake = FakeBedrockClient()
    oversized = "x" * (use_cases.MAX_DOC_CHARS + 100)
    use_cases.summarize_document(fake, oversized)

    sent = fake.last_request["messages"][0]["content"][0]["text"]
    # The prompt wrapper adds some chars, but the doc portion must be capped.
    assert sent.count("x") == use_cases.MAX_DOC_CHARS
