"""REST API endpoints for job description parsing."""

import logging

from fastapi import APIRouter, HTTPException, Depends
from bedrock_poc.models import ParseJobRequest, ParseJobResponse, JobDescription
from bedrock_poc.parsing.job_parser import parse_job_description
from bedrock_poc.auth import User, UserRole, require_any_permission, Permission

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
