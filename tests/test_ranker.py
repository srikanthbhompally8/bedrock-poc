"""Unit tests for semantic ranking module."""

import pytest
from bedrock_poc.matching.matcher import CandidateJobMatch
from bedrock_poc.ranking.ranker import (
    rank_matches,
    calculate_relevance_score,
    calculate_confidence,
    RankedMatch
)


def test_calculate_relevance_score_high():
    """Test relevance score for high match."""
    match = CandidateJobMatch(
        candidate_name="John Doe",
        job_title="Engineer",
        match_score=0.85,
        skill_matches=3,
        missing_skills=[],
        experience_match=1.0,
        education_match=1.0,
        overall_assessment="Excellent"
    )

    score = calculate_relevance_score(match)
    assert score >= 0.7


def test_calculate_relevance_score_low():
    """Test relevance score for low match."""
    match = CandidateJobMatch(
        candidate_name="Jane Doe",
        job_title="Engineer",
        match_score=0.3,
        skill_matches=0,
        missing_skills=["Python", "PostgreSQL", "AWS"],
        experience_match=0.0,
        education_match=0.0,
        overall_assessment="Poor"
    )

    score = calculate_relevance_score(match)
    assert score < 0.3


def test_calculate_confidence_high_data():
    """Test confidence with complete candidate data."""
    match = CandidateJobMatch(
        candidate_name="John Doe",
        job_title="Engineer",
        match_score=0.8,
        skill_matches=3,
        missing_skills=[],
        experience_match=1.0,
        education_match=1.0,
        overall_assessment="Excellent"
    )

    relevance = calculate_relevance_score(match)
    confidence = calculate_confidence(match, relevance)

    assert confidence >= 0.7


def test_calculate_confidence_low_data():
    """Test confidence with incomplete candidate data."""
    match = CandidateJobMatch(
        candidate_name="Jane Doe",
        job_title="Engineer",
        match_score=0.3,
        skill_matches=0,
        missing_skills=["Python"],
        experience_match=0.0,
        education_match=0.0,
        overall_assessment="Poor"
    )

    relevance = calculate_relevance_score(match)
    confidence = calculate_confidence(match, relevance)

    assert confidence < 0.7


def test_rank_matches_sorts_correctly():
    """Test that matches are ranked by relevance."""
    matches = [
        CandidateJobMatch(
            candidate_name="Low Match",
            job_title="Engineer",
            match_score=0.3,
            skill_matches=0,
            missing_skills=["Python"],
            experience_match=0.0,
            education_match=0.0,
            overall_assessment="Poor"
        ),
        CandidateJobMatch(
            candidate_name="High Match",
            job_title="Engineer",
            match_score=0.9,
            skill_matches=5,
            missing_skills=[],
            experience_match=1.0,
            education_match=1.0,
            overall_assessment="Excellent"
        )
    ]

    ranked = rank_matches(matches)

    assert ranked[0].candidate_name == "High Match"
    assert ranked[0].rank == 1
    assert ranked[1].candidate_name == "Low Match"
    assert ranked[1].rank == 2


def test_ranked_match_model():
    """Test RankedMatch model creation."""
    match = RankedMatch(
        rank=1,
        candidate_name="John Doe",
        job_title="Engineer",
        match_score=0.85,
        relevance_score=0.80,
        confidence=0.90,
        assessment="Excellent match",
        reasoning="Strong candidate with all required skills"
    )

    assert match.rank == 1
    assert match.candidate_name == "John Doe"
    assert match.relevance_score == 0.80
    assert match.confidence == 0.90


def test_rank_matches_multiple():
    """Test ranking with multiple candidates."""
    matches = [
        CandidateJobMatch(
            candidate_name="Candidate A",
            job_title="Engineer",
            match_score=0.7,
            skill_matches=2,
            missing_skills=["Docker"],
            experience_match=0.8,
            education_match=1.0,
            overall_assessment="Good"
        ),
        CandidateJobMatch(
            candidate_name="Candidate B",
            job_title="Engineer",
            match_score=0.8,
            skill_matches=3,
            missing_skills=[],
            experience_match=1.0,
            education_match=1.0,
            overall_assessment="Excellent"
        ),
        CandidateJobMatch(
            candidate_name="Candidate C",
            job_title="Engineer",
            match_score=0.5,
            skill_matches=1,
            missing_skills=["Python", "PostgreSQL"],
            experience_match=0.5,
            education_match=0.0,
            overall_assessment="Fair"
        )
    ]

    ranked = rank_matches(matches)

    assert len(ranked) == 3
    assert ranked[0].candidate_name == "Candidate B"  # Best match
    assert ranked[0].rank == 1
    assert ranked[2].rank == 3
