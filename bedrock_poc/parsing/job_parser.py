"""Job description parser using Claude."""

import json
import re
from bedrock_poc.client import build_client, converse
from bedrock_poc.models import JobDescription


def parse_job_description(text: str) -> JobDescription:
    """Parse job description into structured format.

    Args:
        text: Raw job description text to parse

    Returns:
        JobDescription object with extracted structured data

    Raises:
        ValueError: If text is too short or parsing fails
    """
    # Sanitize input
    if not text:
        raise ValueError("Job description cannot be empty")

    text = str(text).strip()

    if len(text) < 10:
        raise ValueError(f"Job description too short ({len(text)} chars, minimum 10 required)")

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
        clean_response = response.strip()

        # Find the start of JSON object
        json_start = clean_response.find('{')
        if json_start < 0:
            raise ValueError("No JSON object found in response")

        # Count braces to find the end
        brace_count = 0
        json_end = -1
        for i in range(json_start, len(clean_response)):
            if clean_response[i] == '{':
                brace_count += 1
            elif clean_response[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break

        if json_end <= json_start:
            raise ValueError("Could not find complete JSON object")

        json_str = clean_response[json_start:json_end]
        data = json.loads(json_str)
        try:
            return JobDescription(**data)
        except Exception as e:
            raise ValueError(f"Failed to create JobDescription from parsed data: {e}. Data was: {data}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse job description response: {response}")
