"""Data models for structured output from Bedrock."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List


class ResumeParsed(BaseModel):
    """Structured representation of a resume."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "John Doe",
                "email": "john@example.com",
                "phone": "123-456-7890",
                "summary": "Senior Software Engineer with 10 years of experience",
                "skills": ["Python", "AWS", "Bedrock", "Docker"],
                "experience": [
                    {
                        "company": "Tech Corp",
                        "title": "Senior Engineer",
                        "dates": "2020-Present",
                        "description": "Led AI/ML initiatives"
                    }
                ],
                "education": [
                    {
                        "degree": "B.S.",
                        "field": "Computer Science",
                        "school": "MIT",
                        "year": 2012
                    }
                ]
            }
        }
    )

    full_name: str = Field(..., description="Candidate's full name")
    email: str = Field(..., description="Email address")
    phone: str = Field(default="", description="Phone number if available")
    summary: str = Field(default="", description="Professional summary or objective")

    skills: list[str] = Field(
        default_factory=list,
        description="List of key skills and competencies"
    )

    experience: list[dict] = Field(
        default_factory=list,
        description="Work experience entries with company, title, dates, and description"
    )

    education: list[dict] = Field(
        default_factory=list,
        description="Education entries with degree, school, year, and major"
    )


class Skill(BaseModel):
    """Represents a skill with proficiency level and importance."""

    name: str = Field(..., description="Skill name (e.g., Python, AWS)")
    proficiency: str = Field(..., description="Proficiency level: beginner, intermediate, or expert")
    importance: int = Field(..., ge=1, le=10, description="Importance score from 1-10")


class JobDescription(BaseModel):
    """Structured representation of a parsed job description."""

    job_title: str = Field(..., description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    years_required: int = Field(..., ge=0, description="Years of experience required")
    core_skills: List[Skill] = Field(default_factory=list, description="Required core skills")
    nice_to_have: List[str] = Field(default_factory=list, description="Nice-to-have skills")
    education: str = Field(..., description="Required education level")
    salary_min: Optional[int] = Field(None, description="Minimum salary")
    salary_max: Optional[int] = Field(None, description="Maximum salary")


class ParseJobRequest(BaseModel):
    """Request model for job parsing API endpoint."""

    job_description: str = Field(..., description="Raw job description text to parse", min_length=10)


class ParseJobResponse(BaseModel):
    """Response model for job parsing API endpoint."""

    status: str = Field(..., description="Response status: success or error")
    data: Optional[JobDescription] = Field(None, description="Parsed job data (null if error)")
    message: Optional[str] = Field(None, description="Error message if status is error")
