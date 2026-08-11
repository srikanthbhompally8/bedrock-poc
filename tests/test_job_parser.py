"""Unit tests for job description parser."""

import pytest
import json
from unittest.mock import patch, MagicMock
from bedrock_poc.parsing.job_parser import parse_job_description, JobDescription, Skill


def test_parse_valid_job_description():
    """Test parsing a valid job description."""
    text = """
    Senior Python Engineer needed at TechCorp.
    5+ years experience required.
    Must know: Python (expert), PostgreSQL (intermediate), AWS (intermediate)
    Nice to have: Kubernetes, Machine Learning
    BS Computer Science required
    Salary: $120k-$160k
    """

    # Mock response from Bedrock
    mock_response = {
        "job_title": "Senior Python Engineer",
        "company": "TechCorp",
        "years_required": 5,
        "core_skills": [
            {"name": "Python", "proficiency": "expert", "importance": 9},
            {"name": "PostgreSQL", "proficiency": "intermediate", "importance": 8},
            {"name": "AWS", "proficiency": "intermediate", "importance": 7}
        ],
        "nice_to_have": ["Kubernetes", "Machine Learning"],
        "education": "BS Computer Science",
        "salary_min": 120000,
        "salary_max": 160000
    }

    with patch('bedrock_poc.parsing.job_parser.converse', return_value=json.dumps(mock_response)):
        result = parse_job_description(text)

        assert isinstance(result, JobDescription)
        assert result.job_title == "Senior Python Engineer"
        assert result.company == "TechCorp"
        assert result.years_required == 5
        assert len(result.core_skills) == 3
        assert result.core_skills[0].name == "Python"
        assert result.core_skills[0].proficiency == "expert"
        assert len(result.nice_to_have) == 2


def test_parse_rejects_empty_description():
    """Test parsing empty description raises error."""
    with pytest.raises(ValueError):
        parse_job_description("")


def test_parse_rejects_short_description():
    """Test parsing too-short description raises error."""
    with pytest.raises(ValueError):
        parse_job_description("Short")


def test_skill_model_validation():
    """Test Skill model validation."""
    skill = Skill(name="Python", proficiency="expert", importance=9)
    assert skill.name == "Python"
    assert skill.proficiency == "expert"
    assert skill.importance == 9


def test_job_description_model_validation():
    """Test JobDescription model validation."""
    job = JobDescription(
        job_title="Senior Engineer",
        years_required=5,
        core_skills=[
            Skill(name="Python", proficiency="expert", importance=9)
        ],
        nice_to_have=["Kubernetes"],
        education="BS Computer Science"
    )

    assert job.job_title == "Senior Engineer"
    assert len(job.core_skills) == 1
    assert job.core_skills[0].name == "Python"


def test_job_description_with_optional_fields():
    """Test JobDescription with optional salary fields."""
    job = JobDescription(
        job_title="Engineer",
        years_required=3,
        core_skills=[],
        nice_to_have=[],
        education="BS",
        salary_min=100000,
        salary_max=150000
    )

    assert job.salary_min == 100000
    assert job.salary_max == 150000
