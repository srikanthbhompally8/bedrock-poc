"""Integration tests for job parsing API endpoint."""

import pytest
import json
from unittest.mock import patch
from fastapi.testclient import TestClient
from bedrock_poc.models import JobDescription, Skill, ParseJobRequest, ParseJobResponse


# Mock app for testing
from fastapi import FastAPI
from bedrock_poc.api.jobs import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_parse_job_endpoint_success():
    """Test successful job parsing via API endpoint."""
    mock_response = {
        "job_title": "Senior Python Engineer",
        "company": "TechCorp",
        "years_required": 5,
        "core_skills": [
            {"name": "Python", "proficiency": "expert", "importance": 9},
            {"name": "AWS", "proficiency": "intermediate", "importance": 8}
        ],
        "nice_to_have": ["Kubernetes"],
        "education": "BS Computer Science",
        "salary_min": 120000,
        "salary_max": 160000
    }

    with patch('bedrock_poc.api.jobs.parse_job_description', return_value=JobDescription(**mock_response)):
        response = client.post(
            "/api/jobs/parse",
            json={"job_description": "Senior Python Engineer needed at TechCorp..."}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["job_title"] == "Senior Python Engineer"
        assert data["data"]["years_required"] == 5
        assert len(data["data"]["core_skills"]) == 2


def test_parse_job_endpoint_empty_description():
    """Test API endpoint with empty job description."""
    response = client.post(
        "/api/jobs/parse",
        json={"job_description": ""}
    )

    assert response.status_code == 422  # Validation error


def test_parse_job_endpoint_short_description():
    """Test API endpoint with too-short description."""
    response = client.post(
        "/api/jobs/parse",
        json={"job_description": "short"}
    )

    assert response.status_code == 422  # Validation error


def test_parse_job_endpoint_parsing_error():
    """Test API endpoint when parsing fails."""
    with patch('bedrock_poc.api.jobs.parse_job_description', side_effect=ValueError("Parsing failed")):
        response = client.post(
            "/api/jobs/parse",
            json={"job_description": "Senior Python Engineer needed..."}
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


def test_parse_job_request_model():
    """Test ParseJobRequest model validation."""
    # Valid request
    request = ParseJobRequest(job_description="Senior Python Engineer required")
    assert len(request.job_description) >= 10

    # Invalid - too short
    with pytest.raises(ValueError):
        ParseJobRequest(job_description="short")


def test_parse_job_response_model():
    """Test ParseJobResponse model."""
    job = JobDescription(
        job_title="Engineer",
        years_required=5,
        core_skills=[],
        nice_to_have=[],
        education="BS"
    )

    response = ParseJobResponse(
        status="success",
        data=job,
        message=None
    )

    assert response.status == "success"
    assert response.data.job_title == "Engineer"
    assert response.message is None
