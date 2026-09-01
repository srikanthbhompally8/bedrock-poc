"""Optimized job description parser with retry logic and concurrency controls."""

import json
import re
import asyncio
import logging
from typing import Tuple, Optional
from enum import Enum
import time

from bedrock_poc.client import build_client, converse
from bedrock_poc.models import JobDescription

log = logging.getLogger(__name__)


class FailureCategory(Enum):
    """Categorizes different types of failures for analysis."""
    THROTTLING = "throttling"  # 429 Too Many Requests
    TIMEOUT = "timeout"  # Request timeout or 504
    VALIDATION = "validation"  # Invalid input or parsing failure
    CONNECTION = "connection"  # Network or connection error
    MODEL_ERROR = "model_error"  # Model access or configuration issue
    SUCCESS = "success"


class ParseMetrics:
    """Tracks performance metrics for job parsing."""

    def __init__(self):
        self.total_attempts = 0
        self.successful_parses = 0
        self.failed_parses = 0
        self.total_latency = 0.0
        self.failure_categories = {cat: 0 for cat in FailureCategory}
        self.retry_count = 0
        self.max_latency = 0.0
        self.min_latency = float('inf')

    def record_attempt(self, duration: float, category: FailureCategory):
        """Record a parse attempt."""
        self.total_attempts += 1
        self.total_latency += duration
        self.max_latency = max(self.max_latency, duration)
        self.min_latency = min(self.min_latency, duration)

        if category == FailureCategory.SUCCESS:
            self.successful_parses += 1
        else:
            self.failed_parses += 1

        self.failure_categories[category] += 1

    def record_retry(self):
        """Record a retry attempt."""
        self.retry_count += 1

    def get_summary(self) -> dict:
        """Get a summary of metrics."""
        success_rate = (self.successful_parses / self.total_attempts * 100) if self.total_attempts > 0 else 0
        avg_latency = (self.total_latency / self.total_attempts) if self.total_attempts > 0 else 0

        return {
            "total_attempts": self.total_attempts,
            "successful_parses": self.successful_parses,
            "failed_parses": self.failed_parses,
            "success_rate_percent": success_rate,
            "avg_latency_ms": avg_latency * 1000,
            "min_latency_ms": self.min_latency * 1000 if self.min_latency != float('inf') else 0,
            "max_latency_ms": self.max_latency * 1000,
            "total_retries": self.retry_count,
            "failure_breakdown": {
                cat.value: count for cat, count in self.failure_categories.items()
            }
        }


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff_ms: int = 100,
        max_backoff_ms: int = 5000,
        backoff_multiplier: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.initial_backoff_ms = initial_backoff_ms
        self.max_backoff_ms = max_backoff_ms
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter

    def get_backoff_ms(self, attempt: int) -> int:
        """Calculate backoff time for given attempt number (0-indexed)."""
        backoff = min(
            self.initial_backoff_ms * (self.backoff_multiplier ** attempt),
            self.max_backoff_ms
        )

        if self.jitter:
            import random
            jitter = random.uniform(0, backoff * 0.1)
            backoff += jitter

        return int(backoff)


class ConcurrencyControl:
    """Manages concurrent requests to Bedrock with rate limiting."""

    def __init__(self, max_concurrent: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent

    async def acquire(self):
        """Acquire a slot for a request."""
        await self.semaphore.acquire()

    def release(self):
        """Release a slot after a request completes."""
        self.semaphore.release()

    async def execute_with_concurrency(self, coro):
        """Execute a coroutine with concurrency control."""
        await self.acquire()
        try:
            return await coro
        finally:
            self.release()


def _categorize_error(error: Exception) -> FailureCategory:
    """Categorize an error based on its type and message."""
    error_str = str(error).lower()

    # Bedrock throttling (429)
    if "throttling" in error_str or "429" in error_str or "rate exceeded" in error_str:
        return FailureCategory.THROTTLING

    # Timeout errors
    if "timeout" in error_str or "504" in error_str or "timed out" in error_str:
        return FailureCategory.TIMEOUT

    # Validation errors
    if "validation" in error_str or "invalid" in error_str or "too short" in error_str:
        return FailureCategory.VALIDATION

    # Connection errors
    if "connection" in error_str or "network" in error_str or "dns" in error_str:
        return FailureCategory.CONNECTION

    # Model access errors
    if "model" in error_str or "access denied" in error_str or "enabled" in error_str:
        return FailureCategory.MODEL_ERROR

    # Default to model error for unknown Bedrock errors
    if "bedrock" in error_str:
        return FailureCategory.MODEL_ERROR

    return FailureCategory.CONNECTION


def parse_job_description_with_retry(
    text: str,
    retry_config: Optional[RetryConfig] = None,
    metrics: Optional[ParseMetrics] = None
) -> Tuple[Optional[JobDescription], FailureCategory, Optional[str]]:
    """Parse job description with retry logic.

    Args:
        text: Raw job description text
        retry_config: Retry configuration (uses default if None)
        metrics: Metrics collector (optional)

    Returns:
        Tuple of (JobDescription or None, FailureCategory, error_message or None)
    """
    if retry_config is None:
        retry_config = RetryConfig()

    if metrics is None:
        metrics = ParseMetrics()

    # Sanitize input
    if not text:
        error_msg = "Job description cannot be empty"
        metrics.record_attempt(0.0, FailureCategory.VALIDATION)
        return None, FailureCategory.VALIDATION, error_msg

    text = str(text).strip()
    if len(text) < 10:
        error_msg = f"Job description too short ({len(text)} chars, minimum 10 required)"
        metrics.record_attempt(0.0, FailureCategory.VALIDATION)
        return None, FailureCategory.VALIDATION, error_msg

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
        start_time = time.time()

        try:
            response = converse(client, messages, max_tokens=1024, temperature=0.1)
            duration = time.time() - start_time

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
                job_desc = JobDescription(**data)
                metrics.record_attempt(duration, FailureCategory.SUCCESS)
                return job_desc, FailureCategory.SUCCESS, None
            except Exception as e:
                raise ValueError(f"Failed to create JobDescription: {e}")

        except Exception as e:
            duration = time.time() - start_time
            category = _categorize_error(e)
            error_msg = str(e)

            log.warning(f"Parse attempt {attempt + 1}/{retry_config.max_retries + 1} failed: {error_msg}")

            # Determine if we should retry
            should_retry = (
                attempt < retry_config.max_retries and
                category in [FailureCategory.THROTTLING, FailureCategory.TIMEOUT]
            )

            if should_retry:
                backoff_ms = retry_config.get_backoff_ms(attempt)
                log.info(f"Retrying after {backoff_ms}ms backoff...")
                metrics.record_retry()
                time.sleep(backoff_ms / 1000.0)
            else:
                # Final attempt or non-retryable error
                metrics.record_attempt(duration, category)
                return None, category, error_msg

    # Should not reach here, but just in case
    return None, FailureCategory.CONNECTION, "Max retries exceeded"


async def parse_job_description_async(
    text: str,
    concurrency_control: Optional[ConcurrencyControl] = None,
    retry_config: Optional[RetryConfig] = None,
    metrics: Optional[ParseMetrics] = None
) -> Tuple[Optional[JobDescription], FailureCategory, Optional[str]]:
    """Async version of parse_job_description with concurrency control.

    Args:
        text: Raw job description text
        concurrency_control: Concurrency controller (optional)
        retry_config: Retry configuration (optional)
        metrics: Metrics collector (optional)

    Returns:
        Tuple of (JobDescription or None, FailureCategory, error_message or None)
    """
    async def _parse():
        # Run the synchronous parsing in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            parse_job_description_with_retry,
            text,
            retry_config,
            metrics
        )

    if concurrency_control:
        return await concurrency_control.execute_with_concurrency(_parse())
    else:
        return await _parse()
