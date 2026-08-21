"""Correlation ID tracking for request tracing.

Provides context-local storage for correlation IDs to track requests end-to-end.
"""

import contextvars
import uuid
from typing import Optional

# Context variable for storing correlation ID
_correlation_id_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=None
)


def get_correlation_id() -> str:
    """Get the current request correlation ID.

    Returns:
        Correlation ID for the current request. Generates new one if not set.
    """
    correlation_id = _correlation_id_context.get()
    if not correlation_id:
        correlation_id = generate_correlation_id()
        _correlation_id_context.set(correlation_id)
    return correlation_id


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current request.

    Args:
        correlation_id: Unique identifier for tracking request across services
    """
    _correlation_id_context.set(correlation_id)


def generate_correlation_id() -> str:
    """Generate a new correlation ID.

    Returns:
        Unique correlation ID in format: bedrock-{uuid}
    """
    return f"bedrock-{uuid.uuid4().hex[:12]}"


def reset_correlation_id() -> None:
    """Reset the correlation ID (for testing or request cleanup)."""
    _correlation_id_context.set(None)
