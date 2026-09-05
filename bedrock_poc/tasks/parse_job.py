"""Async job parsing task with retry logic."""

import logging
import json
from datetime import datetime
from celery import shared_task
from bedrock_poc.celery_app import app
from bedrock_poc.config.async_config import ASYNC_CONFIG
from bedrock_poc.client import build_client, converse
from bedrock_poc.models import JobDescription
from bedrock_poc.models_db import JobQueue
from bedrock_poc.database import get_session_factory

SessionLocal = get_session_factory()

logger = logging.getLogger(__name__)

# Bedrock client (shared across retries)
bedrock_client = build_client(region="us-east-2")

JOB_PARSING_PROMPT = """You are an expert at parsing job descriptions. Extract and structure the following information from the job description provided:
1. Job title
2. Company name
3. Years of experience required
4. Core skills required (with proficiency levels)
5. Nice-to-have skills
6. Education requirements
7. Salary range (min and max)

Return the information as structured JSON matching this schema:
{
  "job_title": "string",
  "company": "string or null",
  "years_required": "number or null",
  "core_skills": [{"name": "string", "proficiency": "beginner|intermediate|expert", "importance": 1-10}],
  "nice_to_have": ["string"],
  "education": "string or null",
  "salary_min": "number or null",
  "salary_max": "number or null"
}
"""


@app.task(bind=True, max_retries=ASYNC_CONFIG["max_retries"])
def parse_job_description_async(self, job_id: str, job_description: str, user_id: int):
    """
    Parse job description asynchronously using Bedrock.

    Args:
        job_id: Unique job ID (UUID)
        job_description: Raw job description text
        user_id: User ID who submitted the job

    Returns:
        Parsed job data as dict

    Retries:
        - Exponential backoff for transient errors (429, 504)
        - Max 3 retries with delays: 3s, 9s, 27s
        - Non-retryable errors fail immediately
    """
    db = SessionLocal()

    try:
        # Update status to processing
        job = db.query(JobQueue).filter_by(job_id=job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database")
            raise Exception(f"Job {job_id} not found")

        job.status = "processing"
        db.commit()

        logger.info(f"Processing job {job_id}: {job_description[:100]}...")

        # Call Bedrock API
        result_text = converse(
            client=bedrock_client,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": f"{JOB_PARSING_PROMPT}\n\nJob Description:\n{job_description}"}]
                }
            ],
            system_prompt="You are a job parsing expert. Return ONLY valid JSON, no markdown or extra text.",
            max_tokens=2048,
            temperature=0.3
        )

        # Parse JSON response
        try:
            parsed_data = json.loads(result_text)
            # Validate with Pydantic model
            job_data = JobDescription(**parsed_data)
            result = job_data.model_dump()
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse Bedrock response: {e}")
            raise ValueError(f"Invalid response format from Bedrock: {str(e)}")

        # Update database with success
        job.status = "completed"
        job.result = result
        job.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Job {job_id} completed successfully")
        return result

    except Exception as e:
        error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
        is_retryable = error_code in ["ThrottlingException", "ServiceUnavailable", "RequestLimitExceeded"]

        if is_retryable and self.request.retries < ASYNC_CONFIG["max_retries"]:
            # Calculate exponential backoff
            retry_delay = ASYNC_CONFIG["retry_backoff"][self.request.retries]
            logger.warning(f"Job {job_id} failed (retryable: {error_code}). Retrying in {retry_delay}s...")

            # Update retry count
            job = db.query(JobQueue).filter_by(job_id=job_id).first()
            if job:
                job.retry_count = self.request.retries + 1
                db.commit()

            # Retry with exponential backoff
            raise self.retry(exc=e, countdown=retry_delay)

        else:
            # Non-retryable error or max retries exceeded
            logger.error(f"Job {job_id} failed (non-retryable or max retries): {str(e)}")

            job = db.query(JobQueue).filter_by(job_id=job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)[:500]
                job.retry_count = self.request.retries
                db.commit()

            raise

    finally:
        db.close()
