"""Structured logging module for Bedrock POC application.

Provides centralized, structured JSON logging with correlation IDs and CloudWatch integration.
"""

import logging
from bedrock_poc.logging.config import setup_logging
from bedrock_poc.logging.correlation import get_correlation_id, set_correlation_id

__all__ = ["setup_logging", "get_correlation_id", "set_correlation_id"]

# Set up logging when module is imported
logger = logging.getLogger(__name__)
