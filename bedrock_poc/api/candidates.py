"""Candidate Search API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/candidates", tags=["candidates"])

# Mock candidate database
candidates_db = {
    1: {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "skills": ["Python", "PostgreSQL", "AWS"],
        "experience_years": 5,
        "education": "BS Computer Science"
    },
    2: {
        "id": 2,
        "name": "Jane Smith",
        "email": "jane@example.com",
        "skills": ["Python", "Docker", "Kubernetes"],
        "experience_years": 3,
        "education": "BS Engineering"
    },
    3: {
        "id": 3,
        "name": "Bob Johnson",
        "email": "bob@example.com",
        "skills": ["Java", "Spring Boot", "PostgreSQL"],
        "experience_years": 7,
        "education": "BS"
    }
}


class CandidateResponse(BaseModel):
    id: int
    name: str
    email: str
    skills: List[str]
    experience_years: int
    education: str


class SearchCandidatesRequest(BaseModel):
    query: Optional[str] = None
    skills: Optional[List[str]] = None
    min_experience: Optional[int] = None


@router.get("/", response_model=dict)
def search_candidates(
    skills: Optional[List[str]] = None,
    limit: int = 10
):
    """Search candidates by skills.

    Args:
        skills: List of skills to filter by
        limit: Maximum candidates to return

    Returns:
        List of matching candidates
    """
    results = []

    for candidate in candidates_db.values():
        if skills:
            # Check if candidate has any of the required skills
            if any(skill.lower() in [s.lower() for s in candidate["skills"]] for skill in skills):
                results.append(candidate)
        else:
            results.append(candidate)

        if len(results) >= limit:
            break

    return {
        "total": len(results),
        "candidates": results
    }


@router.post("/search", response_model=dict)
def advanced_search(request: SearchCandidatesRequest):
    """Advanced candidate search with multiple filters.

    Args:
        request: SearchCandidatesRequest with query, skills, min_experience

    Returns:
        Filtered list of candidates
    """
    results = []

    for candidate in candidates_db.values():
        # Check skills filter
        if request.skills:
            if not any(skill.lower() in [s.lower() for s in candidate["skills"]] for skill in request.skills):
                continue

        # Check experience filter
        if request.min_experience:
            if candidate["experience_years"] < request.min_experience:
                continue

        # Check query filter (searches name and email)
        if request.query:
            query_lower = request.query.lower()
            if query_lower not in candidate["name"].lower() and query_lower not in candidate["email"].lower():
                continue

        results.append(candidate)

    return {
        "total": len(results),
        "candidates": results
    }


@router.get("/{candidate_id}", response_model=dict)
def get_candidate(candidate_id: int):
    """Get candidate profile.

    Args:
        candidate_id: ID of the candidate

    Returns:
        Candidate details
    """
    if candidate_id not in candidates_db:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate = candidates_db[candidate_id]
    return {
        "status": "found",
        "candidate": candidate
    }
