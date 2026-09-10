"""Monitoring and metrics module for Bedrock POC application.

Provides Prometheus metrics collection, health checks, and performance monitoring.
"""

from bedrock_poc.monitoring.metrics import (
    api_request_duration,
    api_request_total,
    api_errors_total,
    database_query_duration,
    bedrock_api_duration,
)
from bedrock_poc.monitoring.health import (
    get_health_status,
    get_readiness_status,
    get_detailed_health,
)

__all__ = [
    "api_request_duration",
    "api_request_total",
    "api_errors_total",
    "database_query_duration",
    "bedrock_api_duration",
    "get_health_status",
    "get_readiness_status",
    "get_detailed_health",
]
