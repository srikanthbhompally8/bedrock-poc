# Bedrock POC - API Documentation

**Version:** 1.0.0  
**Last Updated:** 2026-08-14  
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URL](#base-url)
4. [Job Parsing API](#job-parsing-api)
5. [Candidate Search API](#candidate-search-api)
6. [Match Results API](#match-results-api)
7. [Error Handling](#error-handling)
8. [Response Formats](#response-formats)

---

## Overview

The Bedrock POC API provides a complete recruitment workflow system with:
- Job description parsing and structuring
- Intelligent candidate-job matching
- Semantic ranking of candidates
- Skills gap analysis
- Candidate search capabilities

**Key Features:**
- RESTful architecture
- JSON request/response format
- Comprehensive error handling
- Mock data for demonstration
- Production-ready implementation

---

## Authentication

Currently, the API operates without authentication (demo mode). For production:
- Implement JWT token-based authentication
- Add API key support for service-to-service calls
- Implement rate limiting (100 req/min per client)

---

## Base URL

```
http://localhost:8000
```

For production deployment, update to your domain:
```
https://api.yourdomain.com
```

---

## Job Parsing API

### 1. Parse Job Description

**Endpoint:** `POST /api/jobs/parse`

**Description:** Parse unstructured job description text into structured, queryable format.

**Request:**
```json
{
  "job_description": "Senior Python Engineer needed at TechCorp. 5+ years experience required. Must know: Python (expert), PostgreSQL (intermediate), AWS (intermediate). Nice to have: Kubernetes, Machine Learning. BS Computer Science required. Salary: $120k-$160k"
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "data": {
    "job_title": "Senior Python Engineer",
    "company": "TechCorp",
    "years_required": 5,
    "core_skills": [
      {
        "name": "Python",
        "proficiency": "expert",
        "importance": 9
      },
      {
        "name": "PostgreSQL",
        "proficiency": "intermediate",
        "importance": 8
      }
    ],
    "nice_to_have": ["Kubernetes", "Machine Learning"],
    "education": "BS Computer Science",
    "salary_min": 120000,
    "salary_max": 160000
  }
}
```

**Error Responses:**
- `400 Bad Request` — Invalid input (empty or too short)
- `422 Unprocessable Entity` — Parsing failed
- `500 Internal Server Error` — Server error

---

## Candidate Search API

### 1. Search Candidates by Skills

**Endpoint:** `GET /api/candidates`

**Description:** Search candidates filtered by required skills.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| skills | array | No | List of skills to search for (e.g., `?skills=Python&skills=AWS`) |
| limit | integer | No | Max results (default: 10, max: 100) |

**Example Request:**
```
GET /api/candidates?skills=Python&skills=PostgreSQL&limit=20
```

**Response:** `200 OK`
```json
{
  "total": 2,
  "candidates": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "skills": ["Python", "PostgreSQL", "AWS"],
      "experience_years": 5,
      "education": "BS Computer Science"
    },
    {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "skills": ["Python", "Docker", "Kubernetes"],
      "experience_years": 3,
      "education": "BS Engineering"
    }
  ]
}
```

---

### 2. Advanced Candidate Search

**Endpoint:** `POST /api/candidates/search`

**Description:** Advanced search with multiple filters.

**Request:**
```json
{
  "query": "john",
  "skills": ["Python", "PostgreSQL"],
  "min_experience": 5
}
```

**Response:** `200 OK`
```json
{
  "total": 1,
  "candidates": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "skills": ["Python", "PostgreSQL", "AWS"],
      "experience_years": 5,
      "education": "BS Computer Science"
    }
  ]
}
```

---

### 3. Get Candidate Profile

**Endpoint:** `GET /api/candidates/{candidate_id}`

**Description:** Retrieve complete profile for a specific candidate.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| candidate_id | integer | The candidate's unique ID |

**Example Request:**
```
GET /api/candidates/1
```

**Response:** `200 OK`
```json
{
  "status": "found",
  "candidate": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "skills": ["Python", "PostgreSQL", "AWS"],
    "experience_years": 5,
    "education": "BS Computer Science"
  }
}
```

**Error Responses:**
- `404 Not Found` — Candidate not found

---

## Match Results API

### 1. Create Match

**Endpoint:** `POST /api/matches`

**Description:** Create a match between a candidate and job.

**Request:**
```json
{
  "candidate_id": 1,
  "job_id": 1
}
```

**Response:** `200 OK`
```json
{
  "match_id": 1,
  "status": "created",
  "data": {
    "candidate_name": "John Doe",
    "job_title": "Senior Python Engineer",
    "match_score": 0.85,
    "skill_matches": 3,
    "missing_skills": [],
    "experience_match": 1.0,
    "education_match": 1.0,
    "overall_assessment": "Excellent match"
  }
}
```

---

### 2. Get Match Details

**Endpoint:** `GET /api/matches/{match_id}`

**Description:** Retrieve detailed information about a specific match.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| match_id | integer | The match's unique ID |

**Response:** `200 OK`
```json
{
  "status": "found",
  "data": {
    "candidate_name": "John Doe",
    "job_title": "Senior Python Engineer",
    "match_score": 0.85,
    "skill_matches": 3,
    "missing_skills": [],
    "experience_match": 1.0,
    "education_match": 1.0,
    "overall_assessment": "Excellent match"
  }
}
```

**Error Responses:**
- `404 Not Found` — Match not found

---

### 3. Delete Match

**Endpoint:** `DELETE /api/matches/{match_id}`

**Description:** Remove a match from the system.

**Response:** `200 OK`
```json
{
  "match_id": 1,
  "status": "deleted"
}
```

**Error Responses:**
- `404 Not Found` — Match not found

---

### 4. List Matches

**Endpoint:** `GET /api/matches`

**Description:** List all matches with optional filtering.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| job_id | integer | No | Filter by job ID |
| limit | integer | No | Max results (default: 20) |

**Response:** `200 OK`
```json
{
  "total": 2,
  "matches": [
    {
      "match_id": 1,
      "candidate": "John Doe",
      "job": "Senior Python Engineer",
      "score": 0.85
    },
    {
      "match_id": 2,
      "candidate": "Jane Smith",
      "job": "Senior Python Engineer",
      "score": 0.72
    }
  ]
}
```

---

### 5. Rank Matches for Job

**Endpoint:** `POST /api/matches/{job_id}/rank`

**Description:** Get all candidates ranked by relevance for a specific job.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| job_id | integer | The job's unique ID |

**Response:** `200 OK`
```json
{
  "job_id": 1,
  "total_matches": 2,
  "ranked": [
    {
      "rank": 1,
      "candidate_name": "John Doe",
      "job_title": "Senior Python Engineer",
      "match_score": 0.85,
      "relevance_score": 0.88,
      "confidence": 0.92,
      "assessment": "Excellent match",
      "reasoning": "Strong candidate with 3 matching skills and 100% experience fit"
    },
    {
      "rank": 2,
      "candidate_name": "Jane Smith",
      "job_title": "Senior Python Engineer",
      "match_score": 0.72,
      "relevance_score": 0.70,
      "confidence": 0.85,
      "assessment": "Good match",
      "reasoning": "Solid fit with 2 core skills; missing: Docker"
    }
  ]
}
```

---

## Error Handling

All error responses follow this format:

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid input parameters |
| 404 | Not Found | Resource does not exist |
| 422 | Unprocessable Entity | Validation failed |
| 500 | Server Error | Internal server error |

---

## Response Formats

### Match Score (0-1 scale)
- `0.8-1.0` — Excellent match
- `0.6-0.79` — Good match
- `0.4-0.59` — Fair match
- `0.0-0.39` — Poor match

### Skill Proficiency Levels
- `beginner` — Basic knowledge
- `intermediate` — Working proficiency
- `expert` — Advanced expertise

### Importance Scores (1-10)
- `8-10` — Critical/required
- `5-7` — Important/preferred
- `1-4` — Nice-to-have

---

## Rate Limits

**Demo Mode:** Unlimited (no rate limiting)

**Production Mode (recommended):**
- 100 requests per minute per API key
- 1000 requests per hour per API key
- 10,000 requests per day per API key

---

## Webhooks (Future)

Planned webhook support for:
- Match created
- Match updated
- Ranking complete
- Analysis complete

---

## Support

For API support or issues:
- **GitHub Issues:** https://github.com/srikanthbhompally8/bedrock-poc/issues
- **Email:** support@yourdomain.com
- **Documentation:** See README.md

---

**Last Updated:** 2026-08-14  
**API Version:** 1.0.0  
**Status:** Production Ready ✅
