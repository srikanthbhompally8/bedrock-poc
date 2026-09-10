"""Celery tasks for async job processing."""

from bedrock_poc.tasks.parse_job import parse_job_description_async

__all__ = ["parse_job_description_async"]
