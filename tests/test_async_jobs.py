"""Tests for async job parsing functionality."""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from bedrock_poc.models_db import JobQueue
from bedrock_poc.database import SessionLocal
from bedrock_poc.tasks.parse_job import parse_job_description_async
from bedrock_poc.models import JobDescription

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def db_session():
    """Create a test database session."""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return 1


@pytest.fixture
def test_job_description():
    """Sample job description."""
    return """
    Senior Python Engineer
    Company: TechCorp

    We're looking for a Senior Python Engineer with 5+ years of experience.

    Requirements:
    - 5+ years Python experience
    - AWS expertise
    - Docker and Kubernetes
    - Bachelor's degree in Computer Science

    Nice to have:
    - Bedrock/LLM experience
    - Distributed systems

    Salary: $150k-$200k
    """


# ============================================================================
# UNIT TESTS - Celery Task
# ============================================================================

@pytest.mark.asyncio
def test_parse_job_task_success(db_session, test_user_id, test_job_description):
    """Test successful job parsing task."""
    job_id = "test-job-123"

    # Create job in database
    job = JobQueue(
        user_id=test_user_id,
        job_id=job_id,
        job_description=test_job_description,
        status="pending"
    )
    db_session.add(job)
    db_session.commit()

    # Mock Bedrock response
    mock_response = {
        "job_title": "Senior Python Engineer",
        "company": "TechCorp",
        "years_required": 5,
        "core_skills": [
            {"name": "Python", "proficiency": "expert", "importance": 10},
            {"name": "AWS", "proficiency": "expert", "importance": 9}
        ],
        "nice_to_have": ["Bedrock", "Kubernetes"],
        "education": "Bachelor's in Computer Science",
        "salary_min": 150000,
        "salary_max": 200000
    }

    with patch('bedrock_poc.tasks.parse_job.converse', return_value=json.dumps(mock_response)):
        result = parse_job_description_async(job_id, test_job_description, test_user_id)

    # Verify result
    assert result is not None
    assert result["job_title"] == "Senior Python Engineer"
    assert result["company"] == "TechCorp"

    # Verify database updated
    updated_job = db_session.query(JobQueue).filter_by(job_id=job_id).first()
    assert updated_job.status == "completed"
    assert updated_job.result is not None


def test_parse_job_task_retry_on_throttle(db_session, test_user_id, test_job_description):
    """Test that task retries on throttling error."""
    job_id = "test-job-retry"

    job = JobQueue(
        user_id=test_user_id,
        job_id=job_id,
        job_description=test_job_description,
        status="pending"
    )
    db_session.add(job)
    db_session.commit()

    # Mock throttling error (should trigger retry)
    error = Exception("ThrottlingException")
    error.response = {"Error": {"Code": "ThrottlingException"}}

    with patch('bedrock_poc.tasks.parse_job.converse', side_effect=error):
        with pytest.raises(Exception):
            parse_job_description_async(job_id, test_job_description, test_user_id)

    # Verify retry count increased
    updated_job = db_session.query(JobQueue).filter_by(job_id=job_id).first()
    assert updated_job.retry_count > 0


def test_parse_job_task_failure_on_validation_error(db_session, test_user_id, test_job_description):
    """Test that task fails immediately on validation error."""
    job_id = "test-job-validation"

    job = JobQueue(
        user_id=test_user_id,
        job_id=job_id,
        job_description=test_job_description,
        status="pending"
    )
    db_session.add(job)
    db_session.commit()

    # Mock validation error (should NOT retry)
    with patch('bedrock_poc.tasks.parse_job.converse', return_value="invalid json"):
        with pytest.raises(ValueError):
            parse_job_description_async(job_id, test_job_description, test_user_id)

    # Verify job marked as failed
    updated_job = db_session.query(JobQueue).filter_by(job_id=job_id).first()
    assert updated_job.status == "failed"
    assert updated_job.error_message is not None


# ============================================================================
# INTEGRATION TESTS - API Endpoints
# ============================================================================

@pytest.mark.asyncio
async def test_parse_job_async_endpoint_validation(client, test_user_headers):
    """Test async endpoint validates input."""
    response = client.post(
        "/api/jobs/parse-async",
        json={"job_description": "short"},
        headers=test_user_headers
    )

    assert response.status_code == 400


def test_get_job_status_not_found(client, test_user_headers):
    """Test status endpoint for non-existent job."""
    response = client.get(
        "/api/jobs/nonexistent-job/status",
        headers=test_user_headers
    )

    assert response.status_code == 404


def test_get_job_status_pending(db_session, test_user_id, test_job_description):
    """Test status endpoint for pending job."""
    job_id = "test-pending-job"

    job = JobQueue(
        user_id=test_user_id,
        job_id=job_id,
        job_description=test_job_description,
        status="pending"
    )
    db_session.add(job)
    db_session.commit()

    # Verify job exists with correct status
    fetched_job = db_session.query(JobQueue).filter_by(job_id=job_id).first()
    assert fetched_job is not None
    assert fetched_job.status == "pending"
    assert "result" not in fetched_job.__dict__ or fetched_job.result is None


def test_get_job_status_completed(db_session, test_user_id, test_job_description):
    """Test status endpoint for completed job."""
    job_id = "test-completed-job"
    result = {"job_title": "Engineer", "company": "Corp"}

    job = JobQueue(
        user_id=test_user_id,
        job_id=job_id,
        job_description=test_job_description,
        status="completed",
        result=result,
        completed_at=datetime.utcnow()
    )
    db_session.add(job)
    db_session.commit()

    # Verify job was created with result
    fetched_job = db_session.query(JobQueue).filter_by(job_id=job_id).first()
    assert fetched_job is not None
    assert fetched_job.status == "completed"
    assert fetched_job.result == result
