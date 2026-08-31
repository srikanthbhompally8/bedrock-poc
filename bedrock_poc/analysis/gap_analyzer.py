"""Skills gap analysis and learning path recommendations."""

from pydantic import BaseModel
from typing import List, Optional
from bedrock_poc.models import ResumeParsed, JobDescription, Skill


class SkillGap(BaseModel):
    """Individual skill gap with learning recommendations."""

    skill: str
    required_level: str  # "beginner", "intermediate", "expert"
    candidate_level: Optional[str]  # "none", "beginner", "intermediate", "expert"
    priority: str  # "high", "medium", "low"
    estimated_learning_hours: int
    estimated_weeks: int
    suggested_resources: List[str]


class SkillsGapReport(BaseModel):
    """Complete skills gap analysis report."""

    candidate_name: str
    job_title: str
    total_gaps: int
    high_priority_gaps: int
    estimated_total_hours: int
    estimated_total_weeks: int
    gaps: List[SkillGap]
    learning_path: List[str]  # Ordered steps
    strengths: List[str]  # Skills that exceed requirement


def estimate_learning_time(skill_name: str, proficiency_gap: str) -> tuple[int, int]:
    """Estimate learning time for a skill.

    Args:
        skill_name: Name of the skill
        proficiency_gap: Gap level ("none_to_beginner", "beginner_to_intermediate", etc.)

    Returns:
        (hours, weeks) tuple
    """
    # Standard estimates based on skill gap
    estimates = {
        "none_to_beginner": (40, 2),
        "none_to_intermediate": (80, 4),
        "beginner_to_intermediate": (60, 3),
        "intermediate_to_expert": (120, 6),
    }

    return estimates.get(proficiency_gap, (40, 2))


def get_learning_resources(skill: str, target_level: str) -> List[str]:
    """Get suggested learning resources for a skill.

    Args:
        skill: Skill name
        target_level: Target proficiency level

    Returns:
        List of resource suggestions
    """
    # Simplified resource suggestions
    resources = {
        "Python": [
            "Complete Python Bootcamp (Udemy)",
            "Python.org Official Tutorials",
            "Real Python Advanced Courses"
        ],
        "PostgreSQL": [
            "PostgreSQL Official Documentation",
            "SQL Fundamentals (Coursera)",
            "Advanced SQL for Data Analysis"
        ],
        "AWS": [
            "AWS Certified Solutions Architect",
            "A Cloud Guru AWS Training",
            "Hands-on AWS Labs"
        ],
        "Docker": [
            "Docker Documentation & Getting Started",
            "Play with Docker",
            "Docker Advanced Patterns"
        ],
        "Kubernetes": [
            "Kubernetes Official Tutorial",
            "Linux Academy Kubernetes Course",
            "Kubernetes Hands-on Labs"
        ]
    }

    return resources.get(skill, ["Online courses on Udemy/Coursera", "Official documentation"])


def analyze_skills_gap(candidate: ResumeParsed, job: JobDescription) -> SkillsGapReport:
    """Analyze skills gap between candidate and job requirements.

    Args:
        candidate: Parsed candidate resume
        job: Parsed job description

    Returns:
        SkillsGapReport with detailed analysis
    """
    candidate_skills = {s.lower(): "intermediate" for s in candidate.skills}

    gaps = []
    strengths = []
    total_hours = 0
    max_weeks = 0
    high_priority_count = 0

    # Analyze each required skill
    for job_skill in job.core_skills:
        skill_lower = job_skill.name.lower()
        candidate_level = candidate_skills.get(skill_lower)

        if candidate_level is None:
            # Skill completely missing
            hours, weeks = estimate_learning_time(job_skill.name, "none_to_beginner")
            priority = "high" if job_skill.importance >= 8 else "medium"
            if priority == "high":
                high_priority_count += 1

            gap = SkillGap(
                skill=job_skill.name,
                required_level=job_skill.proficiency,
                candidate_level="none",
                priority=priority,
                estimated_learning_hours=hours,
                estimated_weeks=weeks,
                suggested_resources=get_learning_resources(job_skill.name, job_skill.proficiency)
            )
            gaps.append(gap)
            total_hours += hours
            max_weeks = max(max_weeks, weeks)

        elif candidate_level == job_skill.proficiency:
            # Perfect match
            strengths.append(f"{job_skill.name} ({job_skill.proficiency})")

        elif candidate_level == "beginner" and job_skill.proficiency == "intermediate":
            # Minor gap
            hours, weeks = estimate_learning_time(job_skill.name, "beginner_to_intermediate")
            gap = SkillGap(
                skill=job_skill.name,
                required_level=job_skill.proficiency,
                candidate_level=candidate_level,
                priority="medium",
                estimated_learning_hours=hours,
                estimated_weeks=weeks,
                suggested_resources=get_learning_resources(job_skill.name, job_skill.proficiency)
            )
            gaps.append(gap)
            total_hours += hours
            max_weeks = max(max_weeks, weeks)

    # Sort gaps by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    gaps.sort(key=lambda x: priority_order[x.priority])

    # Create learning path
    learning_path = [f"Learn {gap.skill} ({gap.estimated_weeks} weeks)" for gap in gaps]

    return SkillsGapReport(
        candidate_name=candidate.full_name,
        job_title=job.job_title,
        total_gaps=len(gaps),
        high_priority_gaps=high_priority_count,
        estimated_total_hours=total_hours,
        estimated_total_weeks=max_weeks,
        gaps=gaps,
        learning_path=learning_path,
        strengths=strengths
    )
