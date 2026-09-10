"""Asynchronous processing configuration constants."""

import os

ASYNC_CONFIG = {
    # SQS Configuration
    "sqs_queue_name": os.getenv("SQS_QUEUE_NAME", "bedrock-jobs-queue"),
    "aws_region": os.getenv("AWS_SQS_REGION", "us-east-2"),

    # Bedrock Concurrency
    "max_concurrent_bedrock": int(os.getenv("MAX_CONCURRENT_BEDROCK", "10")),
    "job_timeout": int(os.getenv("JOB_TIMEOUT", "120")),

    # Celery Configuration
    "celery_workers": int(os.getenv("CELERY_WORKERS", "5")),

    # Retry Strategy
    "retry_backoff": [3, 9, 27],  # seconds: 3s, 9s, 27s
    "max_retries": 3,
    "result_ttl": 86400,  # 24 hours

    # Retryable Error Codes
    "retryable_errors": {
        429,  # Throttling
        504,  # Gateway timeout
    },
}
