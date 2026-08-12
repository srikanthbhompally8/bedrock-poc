"""REST API endpoints for job description parsing."""

from fastapi import APIRouter, HTTPException
from bedrock_poc.models import ParseJobRequest, ParseJobResponse, JobDescription
from bedrock_poc.parsing.job_parser import parse_job_description

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/parse", response_model=ParseJobResponse)
async def parse_job(request: ParseJobRequest):
    """Parse job description and return structured data.

    Args:
        request: ParseJobRequest with job_description text

    Returns:
        ParseJobResponse with parsed JobDescription or error message

    Raises:
        HTTPException: 400 if validation fails, 500 if parsing fails
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
