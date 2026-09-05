"""REST API endpoints for job description parsing."""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from bedrock_poc.models import ParseJobRequest, ParseJobResponse, JobDescription
from bedrock_poc.parsing.job_parser import parse_job_description
from bedrock_poc.auth import User, UserRole, require_any_permission, Permission, get_current_user
from bedrock_poc.models_db import JobQueue
from bedrock_poc.database import get_session_factory
from bedrock_poc.tasks.parse_job import parse_job_description_async

SessionLocal = get_session_factory()

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/parse", response_model=ParseJobResponse)
async def parse_job(
    request: ParseJobRequest,
    current_user: User = Depends(require_any_permission(Permission.CREATE_JOB, Permission.MANAGE_JOBS))
):
    """Parse job description with built-in retry logic (Recruiter+ only).

    The endpoint handles retries automatically for transient errors (throttling, timeouts).

    Args:
        request: ParseJobRequest with job_description text
        current_user: Current authenticated user (must be recruiter or admin)

    Returns:
        ParseJobResponse with parsed JobDescription or error message

    Raises:
        HTTPException: 400 for validation failures, 503 for transient errors, 500 for permanent failures
    """
    try:
        # Parse with built-in retry logic (3 retries for throttling/timeouts)
        job_data = parse_job_description(request.job_description)

        return ParseJobResponse(
            status="success",
            data=job_data,
            message=None
        )

    except ValueError as e:
        # Validation error (empty input, too short, JSON parse failure, etc.)
        error_msg = str(e)
        if "too short" in error_msg or "empty" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        elif "timeout" in error_msg or "timed out" in error_msg:
            raise HTTPException(status_code=504, detail="Request timeout. Please try again.")
        elif "throttling" in error_msg or "rate exceeded" in error_msg:
            raise HTTPException(status_code=429, detail="Service throttled. Please retry after a delay.")
        else:
            raise HTTPException(status_code=400, detail=error_msg)

    except Exception as e:
        # Unexpected error
        error_msg = str(e)
        log.error(f"Job parsing error: {error_msg}")

        if "timeout" in error_msg.lower():
            raise HTTPException(status_code=503, detail="Service temporarily unavailable. Please try again.")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to parse job description: {error_msg}")


# ============================================================================
# ASYNC ENDPOINT - Submit job for background processing
# ============================================================================

@router.post("/parse-async", status_code=202)
async def parse_job_async(
    request: ParseJobRequest,
    current_user: User = Depends(get_current_user)
):
    """Submit a job description for async parsing (returns immediately).

    Returns 202 Accepted with job_id for polling status.

    Args:
        request: ParseJobRequest with job_description text
        current_user: Current authenticated user

    Returns:
        {
            "job_id": "uuid-string",
            "status": "pending",
            "status_url": "/api/jobs/{job_id}/status"
        }
    """
    # Validate input
    if not request.job_description or len(request.job_description.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description must be at least 10 characters"
        )

    db = SessionLocal()
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Get user ID (handle both User and TokenPayload models)
        user_id = current_user.user_id if hasattr(current_user, 'user_id') else current_user.id

        # Create job record in database
        job = JobQueue(
            user_id=user_id,
            job_id=job_id,
            job_description=request.job_description,
            status="pending"
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Submit async task to Celery
        parse_job_description_async.delay(
            job_id=job_id,
            job_description=request.job_description,
            user_id=user_id
        )

        return {
            "job_id": job_id,
            "status": "pending",
            "status_url": f"/api/jobs/{job_id}/status"
        }

    finally:
        db.close()


# ============================================================================
# STATUS ENDPOINT - Check job status and get results
# ============================================================================

@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Check the status of an async job and retrieve results if complete.

    Args:
        job_id: The job ID returned from /parse-async
        current_user: Current authenticated user

    Returns:
        - If pending/processing: {"job_id": "...", "status": "pending|processing", "created_at": "..."}
        - If completed: {..., "status": "completed", "result": {...}, "completed_at": "..."}
        - If failed: {..., "status": "failed", "error": "...", "retry_count": N}
    """
    db = SessionLocal()
    try:
        # Fetch job
        job = db.query(JobQueue).filter_by(job_id=job_id).first()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        # Verify ownership (user can only see their own jobs)
        user_id = current_user.user_id if hasattr(current_user, 'user_id') else current_user.id
        if job.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this job"
            )

        # Build response based on status
        response = {
            "job_id": job.job_id,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "retry_count": job.retry_count
        }

        if job.status == "completed":
            response["result"] = job.result
            response["completed_at"] = job.completed_at.isoformat()

        elif job.status == "failed":
            response["error"] = job.error_message
            response["completed_at"] = job.completed_at.isoformat() if job.completed_at else None

        return response

    finally:
        db.close()
