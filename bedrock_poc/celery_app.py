"""Celery application and configuration."""

import os
from celery import Celery
from bedrock_poc.config.async_config import ASYNC_CONFIG

# Initialize Celery app
app = Celery(__name__)

# Load configuration from environment and async_config
app.conf.update(
    broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Import tasks to register them
from bedrock_poc.tasks import parse_job

__all__ = ["app"]
