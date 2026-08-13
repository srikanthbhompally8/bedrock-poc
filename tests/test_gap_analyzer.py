"""Unit tests for skills gap analysis."""

import pytest
from bedrock_poc.models import ResumeParsed
from bedrock_poc.parsing.job_parser import JobDescription, Skill
from bedrock_poc.analysis.gap_analyzer import (
    analyze_skills_gap,
    estimate_learning_time,
    SkillsGapReport
)


def test_estimate_learning_time():
    """Test learning time estimation."""
    hours, weeks = estimate_learning_time("Python", "none_to_beginner")

    assert hours == 40
    assert weeks == 2


def test_analyze_skills_gap_no_gaps():
    """Test gap analysis when candidate has all required skills."""
    candidate = ResumeParsed(
        full_name="Expert Developer",
        email="dev@example.com",
        skills=["Python", "PostgreSQL", "AWS"],
        experience=[{"company": "Tech", "title": "Senior"}],
        education=[{"degree": "BS"}]
    )

    job = JobDescription(
        job_title="Python Engineer",
        years_required=3,
        core_skills=[
            Skill(name="Python", proficiency="expert", importance=9),
            Skill(name="PostgreSQL", proficiency="intermediate", importance=8)
        ],
        nice_to_have=[],
        education="BS"
    )

    report = analyze_skills_gap(candidate, job)

    assert report.total_gaps == 0
    assert len(report.strengths) >= 1
    assert report.estimated_total_hours == 0


def test_analyze_skills_gap_significant_gaps():
    """Test gap analysis when candidate lacks required skills."""
    candidate = ResumeParsed(
        full_name="Junior Developer",
        email="junior@example.com",
        skills=["JavaScript"],
        experience=[],
        education=[]
    )

    job = JobDescription(
        job_title="Python Engineer",
        years_required=5,
        core_skills=[
            Skill(name="Python", proficiency="expert", importance=9),
            Skill(name="PostgreSQL", proficiency="expert", importance=9),
            Skill(name="AWS", proficiency="intermediate", importance=7)
        ],
        nice_to_have=[],
        education="BS"
    )

    report = analyze_skills_gap(candidate, job)

    assert report.total_gaps >= 2
    assert report.high_priority_gaps >= 2
    assert report.estimated_total_hours > 100


def test_skills_gap_report_model():
    """Test SkillsGapReport model creation."""
    report = SkillsGapReport(
        candidate_name="John Doe",
        job_title="Engineer",
        total_gaps=2,
        high_priority_gaps=1,
        estimated_total_hours=80,
        estimated_total_weeks=4,
        gaps=[],
        learning_path=["Learn Python (2 weeks)"],
        strengths=["Good foundation in programming"]
    )

    assert report.candidate_name == "John Doe"
    assert report.total_gaps == 2
    assert report.estimated_total_hours == 80


def test_gap_analysis_high_priority():
    """Test that high-importance skill gaps are marked high priority."""
    candidate = ResumeParsed(
        full_name="Developer",
        email="dev@example.com",
        skills=[],
        experience=[],
        education=[]
    )

    job = JobDescription(
        job_title="Engineer",
        years_required=1,
        core_skills=[
            Skill(name="Python", proficiency="expert", importance=9)  # High importance
        ],
        nice_to_have=[],
        education="BS"
    )

    report = analyze_skills_gap(candidate, job)

    assert len(report.gaps) > 0
    assert report.gaps[0].priority == "high"


def test_gap_analysis_learning_path():
    """Test that learning path is generated."""
    candidate = ResumeParsed(
        full_name="Developer",
        email="dev@example.com",
        skills=[],
        experience=[],
        education=[]
    )

    job = JobDescription(
        job_title="Engineer",
        years_required=1,
        core_skills=[
            Skill(name="Python", proficiency="expert", importance=9),
            Skill(name="Docker", proficiency="intermediate", importance=7)
        ],
        nice_to_have=[],
        education="BS"
    )

    report = analyze_skills_gap(candidate, job)

    assert len(report.learning_path) > 0
    assert any("Python" in step for step in report.learning_path)
