"""Unit tests for candidate-to-job matching."""

import pytest
from bedrock_poc.models import ResumeParsed
from bedrock_poc.parsing.job_parser import JobDescription, Skill
from bedrock_poc.matching.matcher import (
    match_candidate_to_job,
    calculate_skill_match,
    score_experience,
    calculate_total_match
)


def test_calculate_skill_match():
    """Test skill matching calculation."""
    candidate_skills = ["Python", "PostgreSQL", "AWS", "Docker"]
    job_skills = [
        Skill(name="Python", proficiency="expert", importance=9),
        Skill(name="PostgreSQL", proficiency="intermediate", importance=8),
        Skill(name="Kubernetes", proficiency="intermediate", importance=7)
    ]

    matched, missing = calculate_skill_match(candidate_skills, job_skills)

    assert matched == 2
    assert "kubernetes" in [s.lower() for s in missing]


def test_score_experience_exceeds():
    """Test experience scoring when candidate exceeds requirement."""
    score = score_experience(10, 5)
    assert score == 1.0


def test_score_experience_meets():
    """Test experience scoring when candidate meets requirement."""
    score = score_experience(5, 5)
    assert score == 1.0


def test_score_experience_below():
    """Test experience scoring when candidate is below requirement."""
    score = score_experience(3, 5)
    assert 0.0 < score < 1.0
    assert score == pytest.approx(0.6, rel=0.01)


def test_score_experience_none():
    """Test experience scoring when candidate has no experience data."""
    score = score_experience(None, 5)
    assert score == 0.0


def test_calculate_total_match():
    """Test total match score calculation."""
    score = calculate_total_match(0.8, 1.0, 1.0)

    # Should be weighted: 0.8*0.5 + 1.0*0.3 + 1.0*0.2 = 0.9
    assert score == pytest.approx(0.9, rel=0.01)


def test_match_candidate_to_job_excellent():
    """Test matching when candidate is excellent fit."""
    candidate = ResumeParsed(
        full_name="John Doe",
        email="john@example.com",
        skills=["Python", "PostgreSQL", "AWS"],
        experience=[{"company": "Tech Corp", "title": "Senior Engineer"}],
        education=[{"degree": "BS", "field": "Computer Science"}]
    )

    job = JobDescription(
        job_title="Senior Python Engineer",
        years_required=5,
        core_skills=[
            Skill(name="Python", proficiency="expert", importance=9),
            Skill(name="PostgreSQL", proficiency="intermediate", importance=8),
            Skill(name="AWS", proficiency="intermediate", importance=7)
        ],
        nice_to_have=[],
        education="BS Computer Science"
    )

    result = match_candidate_to_job(candidate, job)

    assert result.candidate_name == "John Doe"
    assert result.job_title == "Senior Python Engineer"
    assert result.match_score >= 0.7
    assert result.skill_matches >= 2
    assert len(result.missing_skills) <= 1


def test_match_candidate_to_job_poor():
    """Test matching when candidate is poor fit."""
    candidate = ResumeParsed(
        full_name="Jane Doe",
        email="jane@example.com",
        skills=["JavaScript", "React"],
        experience=[],
        education=[]
    )

    job = JobDescription(
        job_title="Senior Python Engineer",
        years_required=5,
        core_skills=[
            Skill(name="Python", proficiency="expert", importance=9),
            Skill(name="PostgreSQL", proficiency="intermediate", importance=8)
        ],
        nice_to_have=[],
        education="BS"
    )

    result = match_candidate_to_job(candidate, job)

    assert result.match_score < 0.5
    assert result.skill_matches == 0
    assert len(result.missing_skills) >= 2


def test_match_assessment_good():
    """Test assessment text for good match."""
    candidate = ResumeParsed(
        full_name="John Doe",
        email="john@example.com",
        skills=["Python", "PostgreSQL"],
        experience=[{"company": "Tech Corp", "title": "Senior Engineer"}],
        education=[{"degree": "BS"}]
    )

    job = JobDescription(
        job_title="Engineer",
        years_required=1,
        core_skills=[Skill(name="Python", proficiency="expert", importance=9)],
        nice_to_have=[],
        education="BS"
    )

    result = match_candidate_to_job(candidate, job)

    assert "Good" in result.overall_assessment
    assert result.match_score >= 0.6
