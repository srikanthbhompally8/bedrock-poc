"""Thin, model-agnostic wrapper around the Amazon Bedrock ``Converse`` API.

Why the Converse API (and not ``invoke_model``): ``converse`` gives one uniform
request/response shape across every Bedrock chat model — system prompts, multi-turn
message history, and generation settings all use the same schema. That keeps this POC
free of model-specific JSON body formats, so switching models is a config change, not
a code change.

Everything here is plain functions. Callers build a client once with
:func:`build_client` and pass it into :func:`converse` / :func:`converse_stream`.
"""

from __future__ import annotations

import logging
import os
from typing import Iterator

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

# Module logger — configured by the entry points (CLI / web app), not here, so that
# importing this module never changes the host application's logging setup.
log = logging.getLogger(__name__)

# Default Bedrock model. Bedrock model IDs (and whether they need a region-prefixed
# "inference profile" ID like ``us.anthropic...``) vary by account and region, so this
# is only a starting point — override it with the BEDROCK_MODEL_ID environment variable
# to match a model you have enabled in the Bedrock console under "Model access".
DEFAULT_MODEL_ID = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"

# Default AWS region for the Bedrock runtime endpoint. Overridable via AWS_REGION.
DEFAULT_REGION = "us-east-1"


def get_model_id() -> str:
    """Return the Bedrock model ID to use.

    Reads ``BEDROCK_MODEL_ID`` from the environment, falling back to
    :data:`DEFAULT_MODEL_ID`. Kept as a function (not a constant) so the CLI and web UI
    can surface the value that will actually be used.

    Returns:
        The resolved Bedrock model identifier.
    """
    return os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)


def build_client(region: str | None = None):
    """Create a configured ``bedrock-runtime`` boto3 client.

    Args:
        region: AWS region for the Bedrock runtime endpoint. Falls back to the
            ``AWS_REGION`` environment variable, then :data:`DEFAULT_REGION`.

    Returns:
        A ready-to-use boto3 ``bedrock-runtime`` client.

    Raises:
        RuntimeError: If the client could not be created (e.g. missing/invalid AWS
            configuration). We convert the low-level boto error into a clear message
            so the operator sees "what to fix", not a stack trace.
    """
    # Resolve the region from the argument, then the environment, then the default.
    resolved_region = region or os.environ.get("AWS_REGION", DEFAULT_REGION)

    # Bounded retries + timeouts so a flaky network fails fast with a clear error
    # instead of hanging a demo. "standard" mode adds retries for throttling.
    boto_config = Config(
        region_name=resolved_region,
        retries={"max_attempts": 3, "mode": "standard"},
        read_timeout=60,
        connect_timeout=10,
    )

    try:
        # boto3 resolves credentials from the standard chain (env vars, shared config,
        # SSO, instance/task role) — this POC never handles secrets itself.
        client = boto3.client("bedrock-runtime", config=boto_config)
        log.info("Created bedrock-runtime client in region %s", resolved_region)
        return client
    except (BotoCoreError, ClientError) as err:
        # Wrap the AWS SDK error in an actionable message for the operator.
        raise RuntimeError(
            f"Could not create the Bedrock client in region '{resolved_region}'. "
            f"Check your AWS credentials and region configuration. Cause: {err}"
        ) from err


def _build_request(
    messages: list[dict],
    system_prompt: str | None,
    max_tokens: int,
    temperature: float,
) -> dict:
    """Assemble the keyword arguments for a Bedrock ``converse`` call.

    Kept separate so both the buffered (:func:`converse`) and streaming
    (:func:`converse_stream`) paths build identical requests.

    Args:
        messages: Conversation turns in Bedrock Converse shape, e.g.
            ``[{"role": "user", "content": [{"text": "hello"}]}]``.
        system_prompt: Optional system instruction steering the model's behavior.
        max_tokens: Upper bound on tokens the model may generate.
        temperature: Sampling temperature (0 = deterministic, higher = more varied).

    Returns:
        A dict of keyword arguments suitable for ``client.converse(**kwargs)``.
    """
    # inferenceConfig carries generation controls shared by all Converse models.
    request: dict = {
        "modelId": get_model_id(),
        "messages": messages,
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
    }

    # The Converse API expects the system prompt as a list of content blocks, and only
    # when one is actually provided — omit the key entirely otherwise.
    if system_prompt:
        request["system"] = [{"text": system_prompt}]

    return request


def converse(
    client,
    messages: list[dict],
    system_prompt: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> str:
    """Send a conversation to Bedrock and return the full assistant reply as text.

    This is the buffered (non-streaming) path: it waits for the complete response.
    Use it for the CLI's one-shot commands and anywhere a single string is simplest.

    Args:
        client: A ``bedrock-runtime`` client from :func:`build_client`.
        messages: Conversation turns in Bedrock Converse shape.
        system_prompt: Optional system instruction.
        max_tokens: Max tokens to generate.
        temperature: Sampling temperature.

    Returns:
        The assistant's reply as plain text.

    Raises:
        RuntimeError: On any Bedrock/network error, wrapped with a readable message.
    """
    request = _build_request(messages, system_prompt, max_tokens, temperature)

    try:
        response = client.converse(**request)
    except ClientError as err:
        # ClientError covers service-side problems: access denied to the model,
        # throttling, an unknown model ID, etc. Surface the AWS error code because it
        # tells the operator exactly which of those it is.
        code = err.response.get("Error", {}).get("Code", "Unknown")
        raise RuntimeError(
            f"Bedrock request failed ({code}). "
            f"Confirm the model '{get_model_id()}' is enabled in this region and that "
            f"your IAM role allows bedrock:InvokeModel. Cause: {err}"
        ) from err
    except BotoCoreError as err:
        # BotoCoreError covers client-side/networking problems (timeouts, DNS, etc.).
        raise RuntimeError(f"Bedrock request failed due to a network/SDK error: {err}") from err

    # Walk the Converse response envelope down to the text. The reply is a list of
    # content blocks; we concatenate the text of each so multi-block replies are intact.
    content_blocks = response["output"]["message"]["content"]
    reply_text = "".join(block.get("text", "") for block in content_blocks)
    return reply_text.strip()


def converse_stream(
    client,
    messages: list[dict],
    system_prompt: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> Iterator[str]:
    """Stream an assistant reply from Bedrock, yielding text chunks as they arrive.

    This powers the "typewriter" effect in the chat UI: the caller can print or render
    each chunk the moment it's produced instead of waiting for the whole reply.

    Args:
        client: A ``bedrock-runtime`` client from :func:`build_client`.
        messages: Conversation turns in Bedrock Converse shape.
        system_prompt: Optional system instruction.
        max_tokens: Max tokens to generate.
        temperature: Sampling temperature.

    Yields:
        Successive text fragments of the assistant's reply, in order.

    Raises:
        RuntimeError: On any Bedrock/network error, wrapped with a readable message.
    """
    request = _build_request(messages, system_prompt, max_tokens, temperature)

    try:
        response = client.converse_stream(**request)
        # The streaming response is an event iterator. Only "contentBlockDelta" events
        # carry generated text; other events (metadata, start/stop markers) are skipped.
        for event in response["stream"]:
            if "contentBlockDelta" in event:
                delta_text = event["contentBlockDelta"]["delta"].get("text", "")
                if delta_text:
                    yield delta_text
    except ClientError as err:
        code = err.response.get("Error", {}).get("Code", "Unknown")
        raise RuntimeError(
            f"Bedrock streaming request failed ({code}). "
            f"Confirm the model '{get_model_id()}' is enabled and your IAM role allows "
            f"bedrock:InvokeModelWithResponseStream. Cause: {err}"
        ) from err
    except BotoCoreError as err:
        raise RuntimeError(f"Bedrock streaming request failed due to a network/SDK error: {err}") from err
