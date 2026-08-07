"""Data models for structured output from Bedrock."""

from pydantic import BaseModel, ConfigDict, Field


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
