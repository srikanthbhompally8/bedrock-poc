"""Match Results API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from bedrock_poc.matching.matcher import CandidateJobMatch
from bedrock_poc.ranking.ranker import rank_matches, RankedMatch

router = APIRouter(prefix="/api/matches", tags=["matches"])

# In-memory storage for demo (replace with database in production)
matches_db = {}
match_id_counter = 1


class CreateMatchRequest(BaseModel):
    candidate_id: int
    job_id: int


class MatchResponse(BaseModel):
    match_id: int
    status: str
    data: dict


@router.post("/", response_model=MatchResponse)
def create_match(request: CreateMatchRequest):
    """Create a match between candidate and job.

    Args:
        request: CreateMatchRequest with candidate_id and job_id

    Returns:
        Created match with ID
    """
    global match_id_counter

    # In production, fetch candidate and job from database
    # For now, create a mock match
    match = CandidateJobMatch(
        candidate_name=f"Candidate {request.candidate_id}",
        job_title=f"Job {request.job_id}",
        match_score=0.75,
        skill_matches=3,
        missing_skills=["Kubernetes"],
        experience_match=0.8,
        education_match=1.0,
        overall_assessment="Good match"
    )

    match_id = match_id_counter
    match_id_counter += 1

    matches_db[match_id] = match

    return MatchResponse(
        match_id=match_id,
        status="created",
        data=match.dict()
    )


@router.get("/{match_id}", response_model=dict)
def get_match(match_id: int):
    """Retrieve match details.

    Args:
        match_id: ID of the match

    Returns:
        Match details
    """
    if match_id not in matches_db:
        raise HTTPException(status_code=404, detail="Match not found")

    match = matches_db[match_id]
    return {
        "match_id": match_id,
        "status": "found",
        "data": match.dict()
    }


@router.delete("/{match_id}", response_model=dict)
def delete_match(match_id: int):
    """Delete a match.

    Args:
        match_id: ID of the match to delete

    Returns:
        Deletion confirmation
    """
    if match_id not in matches_db:
        raise HTTPException(status_code=404, detail="Match not found")

    del matches_db[match_id]

    return {
        "match_id": match_id,
        "status": "deleted"
    }


@router.get("/", response_model=dict)
def list_matches(job_id: Optional[int] = None, limit: int = 20):
    """List all matches with optional filtering.

    Args:
        job_id: Optional job ID to filter by
        limit: Maximum matches to return

    Returns:
        List of matches
    """
    matches_list = [
        {
            "match_id": mid,
            "candidate": match.candidate_name,
            "job": match.job_title,
            "score": match.match_score
        }
        for mid, match in list(matches_db.items())[:limit]
    ]

    return {
        "total": len(matches_list),
        "matches": matches_list
    }


@router.post("/{job_id}/rank", response_model=dict)
def rank_matches_for_job(job_id: int):
    """Get ranked list of matches for a job.

    Args:
        job_id: ID of the job

    Returns:
        Ranked matches
    """
    if not matches_db:
        raise HTTPException(status_code=404, detail="No matches found")

    matches_list = list(matches_db.values())
    ranked = rank_matches(matches_list)

    return {
        "job_id": job_id,
        "total_matches": len(ranked),
        "ranked": [m.dict() for m in ranked]
    }
