"""Semantic ranking and relevance scoring for matches."""

from pydantic import BaseModel
from typing import List
from bedrock_poc.matching.matcher import CandidateJobMatch


class RankedMatch(BaseModel):
    """Ranked candidate-job match with confidence score."""

    rank: int
    candidate_name: str
    job_title: str
    match_score: float
    relevance_score: float  # 0-1, based on semantic similarity
    confidence: float  # 0-1, confidence in the match
    assessment: str
    reasoning: str


def calculate_relevance_score(match: CandidateJobMatch) -> float:
    """Calculate semantic relevance based on match components.

    Args:
        match: CandidateJobMatch with scoring details

    Returns:
        Relevance score 0-1
    """
    # Relevance is higher when skills match well AND experience meets requirement
    skill_relevance = match.skill_matches / (len(match.missing_skills) + match.skill_matches + 1)
    experience_relevance = match.experience_match

    # Weight: skills 60%, experience 40%
    relevance = (skill_relevance * 0.6) + (experience_relevance * 0.4)

    return round(min(1.0, max(0.0, relevance)), 2)


def calculate_confidence(match: CandidateJobMatch, relevance_score: float) -> float:
    """Calculate confidence in the match prediction.

    Args:
        match: CandidateJobMatch with details
        relevance_score: Semantic relevance score

    Returns:
        Confidence score 0-1
    """
    # More data points = higher confidence
    has_experience = match.experience_match > 0
    has_education = match.education_match > 0
    has_skills = match.skill_matches > 0

    data_points = sum([has_experience, has_education, has_skills])
    base_confidence = data_points / 3.0  # 0.33 to 1.0

    # Adjust by relevance
    confidence = (base_confidence * 0.4) + (relevance_score * 0.6)

    return round(min(1.0, max(0.0, confidence)), 2)


def generate_ranking_reasoning(match: CandidateJobMatch, relevance_score: float) -> str:
    """Generate human-readable reasoning for the ranking.

    Args:
        match: CandidateJobMatch
        relevance_score: Relevance score

    Returns:
        Reasoning string
    """
    if relevance_score >= 0.8:
        return f"Strong candidate with {match.skill_matches} matching skills and {match.experience_match:.0%} experience fit"
    elif relevance_score >= 0.6:
        return f"Solid fit with {match.skill_matches} core skills; missing: {', '.join(match.missing_skills[:2])}"
    elif relevance_score >= 0.4:
        return f"Potential match requiring skill development in: {', '.join(match.missing_skills[:3])}"
    else:
        return f"Significant skills gap ({len(match.missing_skills)} critical skills missing)"


def rank_matches(matches: List[CandidateJobMatch]) -> List[RankedMatch]:
    """Rank matches by relevance and confidence.

    Args:
        matches: List of CandidateJobMatch objects

    Returns:
        Sorted list of RankedMatch objects
    """
    ranked = []

    for match in matches:
        relevance = calculate_relevance_score(match)
        confidence = calculate_confidence(match, relevance)
        reasoning = generate_ranking_reasoning(match, relevance)

        ranked_match = RankedMatch(
            rank=0,  # Will be set after sorting
            candidate_name=match.candidate_name,
            job_title=match.job_title,
            match_score=match.match_score,
            relevance_score=relevance,
            confidence=confidence,
            assessment=match.overall_assessment,
            reasoning=reasoning
        )
        ranked.append(ranked_match)

    # Sort by relevance score (descending), then by match score
    ranked.sort(
        key=lambda x: (x.relevance_score, x.match_score),
        reverse=True
    )

    # Assign ranks
    for i, match in enumerate(ranked, 1):
        match.rank = i

    return ranked
