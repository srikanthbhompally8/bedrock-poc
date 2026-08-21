"""Prometheus metrics collection for application monitoring."""

from prometheus_client import Counter, Histogram, Gauge
import time
from contextlib import contextmanager
from typing import Generator

# API Metrics
api_request_total = Counter(
    "bedrock_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)

api_request_duration = Histogram(
    "bedrock_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

api_errors_total = Counter(
    "bedrock_api_errors_total",
    "Total API errors",
    ["method", "endpoint", "error_type"],
)

# Database Metrics
database_query_duration = Histogram(
    "bedrock_database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

database_connections = Gauge(
    "bedrock_database_connections_active",
    "Active database connections",
)

# Bedrock API Metrics
bedrock_api_duration = Histogram(
    "bedrock_bedrock_api_duration_seconds",
    "AWS Bedrock API call duration in seconds",
    ["operation"],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0),
)

bedrock_api_errors = Counter(
    "bedrock_bedrock_api_errors_total",
    "Total AWS Bedrock API errors",
    ["operation", "error_type"],
)

bedrock_tokens_used = Counter(
    "bedrock_tokens_used_total",
    "Total tokens used in Bedrock API calls",
    ["operation"],
)

# Cache Metrics
cache_hits = Counter(
    "bedrock_cache_hits_total",
    "Cache hit count",
    ["cache_type"],
)

cache_misses = Counter(
    "bedrock_cache_misses_total",
    "Cache miss count",
    ["cache_type"],
)

# Authentication Metrics
auth_attempts_total = Counter(
    "bedrock_auth_attempts_total",
    "Total authentication attempts",
    ["method", "result"],
)

auth_failures_total = Counter(
    "bedrock_auth_failures_total",
    "Total authentication failures",
    ["method", "reason"],
)

# Business Logic Metrics
job_parsing_total = Counter(
    "bedrock_job_parsing_total",
    "Total job descriptions parsed",
    ["status"],
)

matching_total = Counter(
    "bedrock_matching_total",
    "Total candidate-job matches performed",
    ["result"],
)

ranking_duration = Histogram(
    "bedrock_ranking_duration_seconds",
    "Ranking operation duration in seconds",
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0),
)


@contextmanager
def track_request_duration(method: str, endpoint: str) -> Generator:
    """Context manager to track API request duration.

    Usage:
        with track_request_duration("GET", "/api/candidates"):
            # perform operation
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)


@contextmanager
def track_database_query(operation: str, table: str) -> Generator:
    """Context manager to track database query duration.

    Usage:
        with track_database_query("SELECT", "candidates"):
            # perform query
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        database_query_duration.labels(operation=operation, table=table).observe(duration)


@contextmanager
def track_bedrock_call(operation: str) -> Generator:
    """Context manager to track Bedrock API call duration.

    Usage:
        with track_bedrock_call("parse_job"):
            # call bedrock
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        bedrock_api_duration.labels(operation=operation).observe(duration)
