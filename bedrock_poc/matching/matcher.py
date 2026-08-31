"""Candidate-to-job matching algorithm."""

from pydantic import BaseModel
from typing import List, Optional
from bedrock_poc.models import ResumeParsed, JobDescription, Skill


class CandidateJobMatch(BaseModel):
    """Result of matching a candidate to a job."""

    candidate_name: str
    job_title: str
    match_score: float  # 0-1, higher is better
    skill_matches: int
    missing_skills: List[str]
    experience_match: float  # 0-1
    education_match: float  # 0-1
    overall_assessment: str


def calculate_skill_match(candidate_skills: List[str], job_skills: List[Skill]) -> tuple[int, List[str]]:
    """Calculate skill overlap between candidate and job.

    Args:
        candidate_skills: List of candidate's skills
        job_skills: List of required skills (with proficiency info)

    Returns:
        (matched_count, missing_skills_list)
    """
    job_skill_names = {skill.name.lower() for skill in job_skills}
    candidate_skills_lower = {skill.lower() for skill in candidate_skills}

    matched = len(candidate_skills_lower & job_skill_names)
    missing = list(job_skill_names - candidate_skills_lower)

    return matched, missing


def score_experience(candidate_years: Optional[int], required_years: int) -> float:
    """Score how well candidate's experience matches job requirement.

    Args:
        candidate_years: Years of experience (or None)
        required_years: Years required for job

    Returns:
        Score 0-1 (1.0 = meets or exceeds requirement)
    """
    if candidate_years is None:
        return 0.0

    if candidate_years >= required_years:
        return 1.0

    # Partial credit for being close
    return candidate_years / required_years


def calculate_total_match(
    skill_score: float,
    experience_score: float,
    education_score: float = 0.5
) -> float:
    """Calculate weighted total match score.

    Args:
        skill_score: Skill match percentage (0-1)
        experience_score: Experience match score (0-1)
        education_score: Education match score (0-1)

    Returns:
        Total match score (0-1)
    """
    weights = {"skills": 0.5, "experience": 0.3, "education": 0.2}

    total = (
        skill_score * weights["skills"] +
        experience_score * weights["experience"] +
        education_score * weights["education"]
    )

    return min(1.0, max(0.0, total))


def match_candidate_to_job(
    candidate: ResumeParsed,
    job: JobDescription
) -> CandidateJobMatch:
    """Score how well a candidate matches a job.

    Args:
        candidate: Parsed candidate resume
        job: Parsed job description

    Returns:
        CandidateJobMatch with detailed scoring
    """
    # Calculate skill match
    matched_skills, missing_skills = calculate_skill_match(
        candidate.skills,
        job.core_skills
    )

    total_job_skills = len(job.core_skills)
    skill_score = matched_skills / total_job_skills if total_job_skills > 0 else 0.0

    # Calculate experience match
    candidate_years = getattr(candidate, 'years_experience', None)
    experience_score = score_experience(candidate_years, job.years_required)

    # Calculate education match (simple check)
    education_score = 1.0 if candidate.education else 0.5

    # Calculate total match
    match_score = calculate_total_match(
        skill_score,
        experience_score,
        education_score
    )

    # Generate assessment
    if match_score >= 0.8:
        assessment = "Excellent match"
    elif match_score >= 0.6:
        assessment = "Good match"
    elif match_score >= 0.4:
        assessment = "Fair match"
    else:
        assessment = "Poor match - significant gaps"

    return CandidateJobMatch(
        candidate_name=candidate.full_name,
        job_title=job.job_title,
        match_score=round(match_score, 2),
        skill_matches=matched_skills,
        missing_skills=missing_skills,
        experience_match=round(experience_score, 2),
        education_match=round(education_score, 2),
        overall_assessment=assessment
    )
