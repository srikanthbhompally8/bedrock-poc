"""REST API endpoints for job description parsing."""

from fastapi import APIRouter, HTTPException, Depends
from bedrock_poc.models import ParseJobRequest, ParseJobResponse, JobDescription
from bedrock_poc.parsing.job_parser import parse_job_description
from bedrock_poc.auth import User, UserRole, require_any_permission, Permission

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/parse", response_model=ParseJobResponse)
async def parse_job(
    request: ParseJobRequest,
    current_user: User = Depends(require_any_permission(Permission.CREATE_JOB, Permission.MANAGE_JOBS))
):
    """Parse job description and return structured data (Recruiter+ only).

    Args:
        request: ParseJobRequest with job_description text
        current_user: Current authenticated user (must be recruiter or admin)

    Returns:
        ParseJobResponse with parsed JobDescription or error message

    Raises:
        HTTPException: 400 if validation fails, 500 if parsing fails, 403 if unauthorized
    """
    try:
        # Parse the job description
        job_data = parse_job_description(request.job_description)

        # Return success response
        return ParseJobResponse(
            status="success",
            data=job_data,
            message=None
        )

    except ValueError as e:
        # Validation error (empty input, too short, etc.)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected error (parsing failure, etc.)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse job description: {str(e)}"
        )
