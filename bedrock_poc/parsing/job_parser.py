"""Job description parser using Claude with retry logic and error handling."""

import json
import logging
import time
from enum import Enum

from bedrock_poc.client import build_client, converse
from bedrock_poc.models import JobDescription

log = logging.getLogger(__name__)


class FailureCategory(Enum):
    """Categorizes different types of failures."""
    THROTTLING = "throttling"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    CONNECTION = "connection"
    MODEL_ERROR = "model_error"
    SUCCESS = "success"


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff_ms: int = 100,
        max_backoff_ms: int = 5000,
        backoff_multiplier: float = 2.0
    ):
        self.max_retries = max_retries
        self.initial_backoff_ms = initial_backoff_ms
        self.max_backoff_ms = max_backoff_ms
        self.backoff_multiplier = backoff_multiplier

    def get_backoff_ms(self, attempt: int) -> int:
        """Calculate backoff time for given attempt number."""
        backoff = min(
            self.initial_backoff_ms * (self.backoff_multiplier ** attempt),
            self.max_backoff_ms
        )
        return int(backoff)


def _categorize_error(error: Exception) -> FailureCategory:
    """Categorize an error based on its type and message."""
    error_str = str(error).lower()

    if "throttling" in error_str or "429" in error_str or "rate exceeded" in error_str:
        return FailureCategory.THROTTLING

    if "timeout" in error_str or "504" in error_str or "timed out" in error_str:
        return FailureCategory.TIMEOUT

    if "validation" in error_str or "invalid" in error_str or "too short" in error_str:
        return FailureCategory.VALIDATION

    if "connection" in error_str or "network" in error_str or "dns" in error_str:
        return FailureCategory.CONNECTION

    if "model" in error_str or "access denied" in error_str or "enabled" in error_str:
        return FailureCategory.MODEL_ERROR

    if "bedrock" in error_str:
        return FailureCategory.MODEL_ERROR

    return FailureCategory.CONNECTION


def parse_job_description(
    text: str,
    retry_config: RetryConfig = None
) -> JobDescription:
    """Parse job description into structured format with retry logic.

    Args:
        text: Raw job description text to parse
        retry_config: Retry configuration (uses default if None)

    Returns:
        JobDescription object with extracted structured data

    Raises:
        ValueError: If text is too short or parsing fails after retries
    """
    if retry_config is None:
        retry_config = RetryConfig()

    # Sanitize input
    if not text:
        raise ValueError("Job description cannot be empty")

    text = str(text).strip()

    if len(text) < 10:
        raise ValueError(f"Job description too short ({len(text)} chars, minimum 10 required)")

    client = build_client()

    prompt = f"""Parse this job description and extract structured data.

Return ONLY valid JSON (no markdown, no code blocks) matching this structure:
{{
    "job_title": "Senior Python Engineer",
    "company": "Company Name",
    "years_required": 5,
    "core_skills": [
        {{"name": "Python", "proficiency": "expert", "importance": 9}},
        {{"name": "PostgreSQL", "proficiency": "intermediate", "importance": 8}}
    ],
    "nice_to_have": ["Kubernetes", "Machine Learning"],
    "education": "BS Computer Science",
    "salary_min": 120000,
    "salary_max": 160000
}}

Job Description:
{text}"""

    messages = [{"role": "user", "content": [{"text": prompt}]}]

    # Try parsing with retries
    for attempt in range(retry_config.max_retries + 1):
        try:
            response = converse(client, messages, max_tokens=1024, temperature=0.1)

            # Parse JSON response
            clean_response = response.strip()
            json_start = clean_response.find('{')
            if json_start < 0:
                raise ValueError("No JSON object found in response")

            brace_count = 0
            json_end = -1
            for i in range(json_start, len(clean_response)):
                if clean_response[i] == '{':
                    brace_count += 1
                elif clean_response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break

            if json_end <= json_start:
                raise ValueError("Could not find complete JSON object")

            json_str = clean_response[json_start:json_end]
            data = json.loads(json_str)

            try:
                return JobDescription(**data)
            except Exception as e:
                raise ValueError(f"Failed to create JobDescription: {e}")

        except Exception as e:
            category = _categorize_error(e)
            error_msg = str(e)

            log.warning(f"Parse attempt {attempt + 1}/{retry_config.max_retries + 1} failed ({category.value}): {error_msg}")

            # Determine if we should retry
            should_retry = (
                attempt < retry_config.max_retries and
                category in [FailureCategory.THROTTLING, FailureCategory.TIMEOUT]
            )

            if should_retry:
                backoff_ms = retry_config.get_backoff_ms(attempt)
                log.info(f"Retrying after {backoff_ms}ms backoff...")
                time.sleep(backoff_ms / 1000.0)
            else:
                # Final attempt or non-retryable error
                raise ValueError(error_msg)
