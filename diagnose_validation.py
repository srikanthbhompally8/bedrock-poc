#!/usr/bin/env python3
"""Diagnostic script to identify job parsing validation failures."""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# Set Bedrock model
os.environ['BEDROCK_MODEL_ID'] = 'us.anthropic.claude-haiku-4-5-20251001-v1:0'

from bedrock_poc.client import build_client, converse
from bedrock_poc.models import JobDescription

def diagnose_parsing(job_description: str):
    """Test job parsing and capture detailed validation errors."""

    print(f"\n{'='*80}")
    print(f"Testing job description: {job_description[:50]}...")
    print(f"{'='*80}\n")

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
{job_description}"""

    try:
        # Get response from Claude
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        response = converse(client, messages, max_tokens=1024, temperature=0.1)

        print(f"Claude Response:\n{response}\n")

        # Extract JSON
        clean_response = response.strip()
        json_start = clean_response.find('{')

        if json_start < 0:
            print("ERROR: No JSON object found in response")
            return

        # Find matching brace
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

        json_str = clean_response[json_start:json_end]
        print(f"Extracted JSON:\n{json.dumps(json.loads(json_str), indent=2)}\n")

        # Try to parse into JobDescription
        data = json.loads(json_str)

        # Debug: Show data types
        print("Field Analysis:")
        for key, value in data.items():
            print(f"  {key}: {type(value).__name__} = {value}")
        print()

        # Attempt validation
        try:
            job = JobDescription(**data)
            print("✅ SUCCESS: JobDescription created successfully")
            print(f"Job: {job.job_title} at {job.company}")
        except Exception as e:
            print(f"❌ VALIDATION ERROR: {e}")

            # Try to identify the specific issue
            print("\nDiagnostic Fixes:")

            # Fix 1: Lowercase proficiency
            if 'core_skills' in data:
                for skill in data['core_skills']:
                    if 'proficiency' in skill:
                        skill['proficiency'] = skill['proficiency'].lower()
                print("  → Lowercased proficiency values")

            # Fix 2: Convert years_required to int
            if 'years_required' in data and isinstance(data['years_required'], str):
                data['years_required'] = int(data['years_required'])
                print("  → Converted years_required to int")

            # Fix 3: Ensure required fields exist
            if 'job_title' not in data:
                data['job_title'] = "Unknown"
                print("  → Added missing job_title")

            if 'education' not in data:
                data['education'] = "Not specified"
                print("  → Added missing education")

            # Retry with fixes
            print("\nRetrying with fixes...")
            try:
                job = JobDescription(**data)
                print("✅ SUCCESS after fixes: JobDescription created")
            except Exception as e2:
                print(f"❌ Still failing: {e2}")

    except Exception as e:
        print(f"ERROR: {e}")

# Test with a valid job description
test_job = """
Senior Python Engineer

We're looking for a Senior Python Engineer with 5+ years of experience.
Requirements: Python, FastAPI, PostgreSQL
Nice to have: Docker, Kubernetes
Education: BS Computer Science
Salary: $120,000 - $160,000
"""

diagnose_parsing(test_job)
