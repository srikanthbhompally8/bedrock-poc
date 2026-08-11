"""Job description parser using Claude."""

import json
from pydantic import BaseModel
from typing import List, Optional
from bedrock_poc.client import build_client, converse


class Skill(BaseModel):
    name: str
    proficiency: str  # "beginner", "intermediate", "expert"
    importance: int   # 1-10


class JobDescription(BaseModel):
    job_title: str
    company: Optional[str] = None
    years_required: int
    core_skills: List[Skill]
    nice_to_have: List[str]
    education: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None


def parse_job_description(text: str) -> JobDescription:
    """Parse job description into structured format.

    Args:
        text: Raw job description text to parse

    Returns:
        JobDescription object with extracted structured data

    Raises:
        ValueError: If text is too short or parsing fails
    """
    if not text or len(text.strip()) < 10:
        raise ValueError("Job description must be at least 10 characters")

    client = build_client()

    prompt = f"""Parse this job description and extract structured data.

Return ONLY valid JSON (no markdown, no code blocks) matching this structure:
{{
    "job_title": "Senior Python Engineer",
    "company": "Company Name",
    "years_required": 5,
    "core_skills": [
        {{"name": "Python", "proficiency": "expert", "importance": 9}},
        {{"name": "PostgreSQL", "proficiency": "intermediate", "importance": 8}}
    ],
    "nice_to_have": ["Kubernetes", "Machine Learning"],
    "education": "BS Computer Science",
    "salary_min": 120000,
    "salary_max": 160000
}}

Job Description:
{text}"""

    # Call Claude via Bedrock to parse the job description
    messages = [{"role": "user", "content": [{"text": prompt}]}]
    response = converse(client, messages, max_tokens=1024, temperature=0.1)

    # Parse JSON response and return JobDescription object
    try:
        data = json.loads(response)
        return JobDescription(**data)
    except json.JSONDecodeError:
        raise ValueError(f"Failed to parse job description response: {response}")
