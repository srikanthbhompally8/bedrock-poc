"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from bedrock_poc.api import matches, candidates


def test_create_match():
    """Test creating a match via API."""
    from bedrock_poc.api.matches import router as matches_router

    # Test creating a match
    response = matches.create_match(
        matches.CreateMatchRequest(candidate_id=1, job_id=1)
    )

    assert response.status == "created"
    assert response.match_id > 0
    assert response.data["candidate_name"]
    assert response.data["job_title"]


def test_get_match():
    """Test retrieving a match."""
    # Create a match first
    create_resp = matches.create_match(
        matches.CreateMatchRequest(candidate_id=1, job_id=1)
    )
    match_id = create_resp.match_id

    # Retrieve it
    get_resp = matches.get_match(match_id)

    assert get_resp["status"] == "found"
    assert get_resp["data"]["candidate_name"]


def test_get_match_not_found():
    """Test retrieving non-existent match."""
    with pytest.raises(Exception):
        matches.get_match(9999)


def test_delete_match():
    """Test deleting a match."""
    # Create a match
    create_resp = matches.create_match(
        matches.CreateMatchRequest(candidate_id=1, job_id=1)
    )
    match_id = create_resp.match_id

    # Delete it
    delete_resp = matches.delete_match(match_id)

    assert delete_resp["status"] == "deleted"
    assert delete_resp["match_id"] == match_id


def test_list_matches():
    """Test listing matches."""
    # Create a match
    matches.create_match(
        matches.CreateMatchRequest(candidate_id=1, job_id=1)
    )

    # List matches
    list_resp = matches.list_matches(limit=10)

    assert "matches" in list_resp
    assert list_resp["total"] >= 0


def test_rank_matches():
    """Test ranking matches for a job."""
    # Create matches
    matches.create_match(
        matches.CreateMatchRequest(candidate_id=1, job_id=1)
    )
    matches.create_match(
        matches.CreateMatchRequest(candidate_id=2, job_id=1)
    )

    # Rank them
    rank_resp = matches.rank_matches_for_job(1)

    assert "ranked" in rank_resp
    assert rank_resp["job_id"] == 1
    assert len(rank_resp["ranked"]) > 0


def test_search_candidates_by_skills():
    """Test searching candidates by skills."""
    result = candidates.search_candidates(skills=["Python"], limit=10)

    assert "candidates" in result
    assert result["total"] >= 1
    assert any("Python" in c["skills"] for c in result["candidates"])


def test_search_candidates_advanced():
    """Test advanced candidate search."""
    result = candidates.advanced_search(
        candidates.SearchCandidatesRequest(
            skills=["Python"],
            min_experience=3
        )
    )

    assert "candidates" in result
    assert all(c["experience_years"] >= 3 for c in result["candidates"])


def test_get_candidate():
    """Test retrieving candidate profile."""
    result = candidates.get_candidate(1)

    assert result["status"] == "found"
    assert result["candidate"]["name"] == "John Doe"
    assert "skills" in result["candidate"]


def test_get_candidate_not_found():
    """Test retrieving non-existent candidate."""
    with pytest.raises(Exception):
        candidates.get_candidate(9999)


def test_search_candidates_by_query():
    """Test searching candidates by name/email."""
    result = candidates.advanced_search(
        candidates.SearchCandidatesRequest(query="john")
    )

    assert "candidates" in result
    assert any("John" in c["name"] or "john" in c["email"] for c in result["candidates"])


def test_end_to_end_workflow():
    """Test complete end-to-end workflow."""
    # 1. Search for candidates
    search_result = candidates.search_candidates(skills=["Python"], limit=5)
    assert search_result["total"] > 0

    # 2. Get candidate details
    candidate = candidates.get_candidate(search_result["candidates"][0]["id"])
    assert candidate["status"] == "found"

    # 3. Create a match
    match_result = matches.create_match(
        matches.CreateMatchRequest(
            candidate_id=search_result["candidates"][0]["id"],
            job_id=1
        )
    )
    assert match_result.status == "created"

    # 4. Retrieve match
    get_result = matches.get_match(match_result.match_id)
    assert get_result["status"] == "found"

    # 5. Clean up
    delete_result = matches.delete_match(match_result.match_id)
    assert delete_result["status"] == "deleted"
