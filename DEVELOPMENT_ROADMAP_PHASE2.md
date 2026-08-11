# Development Roadmap - Phase 2: Production Features

**Status:** Phase 1 Complete (Database Integration Ready)  
**Phase 2 Start Date:** 2026-08-10  
**Target Completion:** 2026-09-30  
**Team Size:** 1+ developers  

---

## Overview

Phase 2 focuses on building the AI Recruiter's core matching and analysis capabilities. The environment is now stable with PostgreSQL integration ready, allowing us to build persistent, production-grade features.

### What's Already Done (Phase 1)
- ✅ AWS Bedrock integration
- ✅ Streamlit web UI
- ✅ CLI tools
- ✅ Resume PDF parsing
- ✅ Basic RAG engine
- ✅ PostgreSQL database setup
- ✅ SQLAlchemy ORM models

### What We're Building (Phase 2)
- 🔨 Job description parsing
- 🔨 Advanced semantic matching
- 🔨 Skills gap analysis
- 🔨 Candidate search APIs
- 🔨 Match results APIs
- 🔨 Test coverage expansion
- 🔨 API documentation

---

## Task 1: Job Description Parsing Module

### Goal
Create a module that parses job descriptions and extracts structured data for matching.

### Requirements

**Input:**
- Job description text (100-2000 words)
- Optional: job title, company, salary range

**Output:**
```python
{
    "job_title": "Senior Python Engineer",
    "company": "Acme Corp",
    "level": "senior",
    "years_required": 5,
    
    "core_skills": [
        {"skill": "Python", "proficiency": "expert", "importance": 9},
        {"skill": "PostgreSQL", "proficiency": "intermediate", "importance": 8},
        {"skill": "AWS", "proficiency": "intermediate", "importance": 7}
    ],
    
    "nice_to_have": [
        "Kubernetes",
        "Machine Learning",
        "Leadership experience"
    ],
    
    "education": "BS Computer Science or equivalent",
    "experience_summary": "5+ years building scalable backend systems",
    
    "salary_range": {
        "min": 120000,
        "max": 160000,
        "currency": "USD"
    },
    
    "key_responsibilities": [
        "Design and implement APIs",
        "Mentor junior engineers",
        "Optimize database performance"
    ],
    
    "embedding": [0.123, 0.456, ...]  # Vector embedding for similarity search
}
```

### Implementation Plan

```
1. Create bedrock_poc/parsing/job_parser.py
   - Function: parse_job_description(text: str) -> JobDescription
   - Use Claude to extract and classify requirements
   - Validate output against schema

2. Define data model (bedrock_poc/models.py)
   class JobDescription(BaseModel):
       job_title: str
       core_skills: List[Skill]
       level: str
       years_required: int
       ... etc

3. Create database model (bedrock_poc/models_db.py)
   class JobListing(Base):
       id: Integer
       job_description: Text
       parsed_data: JSON
       embedding: ARRAY(Float)
       created_at: DateTime

4. Create unit tests (tests/test_job_parser.py)
   - Test with sample job descriptions
   - Verify output schema
   - Test error cases

5. Create integration tests
   - Parse -> Store -> Retrieve
   - Verify database persistence
```

### Acceptance Criteria
- [ ] Parses job descriptions with 90%+ accuracy
- [ ] Extracts 8+ core skills with proficiency levels
- [ ] Generates semantic embeddings
- [ ] Stores parsed data in PostgreSQL
- [ ] Unit tests: 95%+ coverage
- [ ] API endpoint: `POST /api/jobs/parse`

### Estimated Effort: 12-16 hours

---

## Task 2: Advanced Matching Engine

### Goal
Implement semantic similarity matching between candidates and jobs.

### Requirements

**Input:**
- Candidate resume (parsed)
- Job description (parsed)
- Matching criteria (threshold, weights)

**Output:**
```python
{
    "match_score": 0.87,  # 0-1, higher = better match
    
    "skill_matches": [
        {
            "skill": "Python",
            "candidate_proficiency": "expert",
            "job_proficiency": "expert",
            "match_level": 1.0
        },
        {
            "skill": "PostgreSQL",
            "candidate_proficiency": "intermediate",
            "job_proficiency": "intermediate",
            "match_level": 0.95
        }
    ],
    
    "experience_match": 0.88,
    "education_match": 0.92,
    
    "gap_areas": [
        "Kubernetes (required but not experienced)"
    ],
    
    "strengths": [
        "Exceeds years of experience requirement",
        "Expert Python developer",
        "Leadership background aligns with senior role"
    ]
}
```

### Implementation Plan

```
1. Create bedrock_poc/matching/matcher.py
   - Class: CandidateMatcher
   - Method: match(resume: Resume, job: JobDescription) -> MatchResult
   - Use semantic similarity for skill matching
   - Weighted scoring for different criteria

2. Semantic matching strategy
   - Convert skills to embeddings
   - Calculate cosine similarity
   - Apply proficiency weighting
   - Score experience alignment

3. Create data model (bedrock_poc/models.py)
   class MatchResult(BaseModel):
       match_score: float
       skill_matches: List[SkillMatch]
       experience_match: float
       education_match: float
       gap_areas: List[str]
       strengths: List[str]

4. Create database model (bedrock_poc/models_db.py)
   class CandidateJobMatch(Base):
       id: Integer
       candidate_id: Integer
       job_id: Integer
       match_score: Float
       details: JSON
       created_at: DateTime

5. Create unit tests (tests/test_matcher.py)
   - Test skill matching algorithm
   - Test scoring edge cases
   - Test gap identification

6. Create integration tests
   - End-to-end: Parse -> Match -> Store
```

### Acceptance Criteria
- [ ] Matches similar skills with >95% accuracy
- [ ] Handles skill proficiency levels
- [ ] Identifies experience gaps
- [ ] Scores match 0-1 range
- [ ] Semantic embedding-based matching
- [ ] Unit tests: 95%+ coverage
- [ ] API endpoint: `POST /api/matches`

### Estimated Effort: 14-18 hours

---

## Task 3: Skills Gap Analysis

### Goal
Analyze and provide actionable skills gap insights.

### Requirements

**Input:**
- Candidate resume
- Target job description

**Output:**
```python
{
    "gaps": [
        {
            "skill": "Kubernetes",
            "job_requirement_level": "intermediate",
            "candidate_level": "none",
            "priority": "high",
            "estimated_learning_hours": 40,
            "resources": [
                {
                    "type": "course",
                    "title": "Kubernetes for Developers",
                    "platform": "Udemy",
                    "url": "https://..."
                }
            ]
        }
    ],
    
    "strengths": [
        {
            "skill": "Python",
            "explanation": "Candidate exceeds requirement"
        }
    ],
    
    "learning_path": [
        {
            "order": 1,
            "skill": "Docker",
            "weeks": 2,
            "effort_hours": 20
        },
        {
            "order": 2,
            "skill": "Kubernetes",
            "weeks": 3,
            "effort_hours": 30
        }
    ],
    
    "total_learning_hours": 50,
    "estimated_timeline_weeks": 6
}
```

### Implementation Plan

```
1. Create bedrock_poc/analysis/gap_analyzer.py
   - Class: SkillsGapAnalyzer
   - Method: analyze(candidate: Resume, job: JobDescription) -> GapAnalysis
   - Compare skill proficiency levels
   - Identify gaps
   - Suggest learning resources

2. Learning resource integration
   - Call Claude API to suggest relevant courses
   - Include platforms: Udemy, Coursera, LinkedIn Learning
   - Provide estimated learning times

3. Create data models (bedrock_poc/models.py)
   class SkillGap(BaseModel):
       skill: str
       gap_level: str  # "high", "medium", "low"
       resources: List[LearningResource]

4. Create database model (bedrock_poc/models_db.py)
   class SkillsGapReport(Base):
       id: Integer
       candidate_id: Integer
       job_id: Integer
       gap_analysis: JSON
       created_at: DateTime

5. Create unit tests (tests/test_gap_analyzer.py)
   - Test gap identification
   - Test learning path generation
   - Test resource suggestions

6. Create integration tests
   - End-to-end analysis flow
```

### Acceptance Criteria
- [ ] Identifies all skill gaps correctly
- [ ] Suggests appropriate learning resources
- [ ] Estimates learning time accurately
- [ ] Prioritizes gaps by importance
- [ ] Provides actionable recommendations
- [ ] Unit tests: 95%+ coverage
- [ ] API endpoint: `POST /api/analysis/gaps`

### Estimated Effort: 10-14 hours

---

## Task 4: Candidate Search & Filter API

### Goal
Enable efficient searching and filtering of candidates.

### Requirements

**Endpoints:**
```
GET /api/candidates - Search candidates
  Query params:
    - skills: List[str] - Filter by skills
    - min_experience: int - Years of experience
    - job_id: int - Match against job
    - limit: int = 10
    - offset: int = 0

POST /api/candidates/search - Advanced search
  Body:
    {
      "query": "Python expert with AWS experience",
      "skills": ["Python", "AWS"],
      "min_years": 5,
      "max_years": 15,
      "education": "BS Computer Science"
    }

GET /api/candidates/{candidate_id} - Get candidate profile
  Response:
    {
      "id": int,
      "name": str,
      "email": str,
      "skills": List[str],
      "experience_years": int,
      "recent_matches": List[MatchResult]
    }
```

### Implementation Plan

```
1. Create bedrock_poc/repositories/candidate_repo.py
   - Class: CandidateRepository
   - Method: search(criteria) -> List[Candidate]
   - Use database queries and vector similarity

2. Create API routes (app.py or separate routes file)
   - GET /api/candidates
   - POST /api/candidates/search
   - GET /api/candidates/{id}

3. Create Pydantic models for requests/responses

4. Implement filtering logic
   - Skills matching (exact + semantic)
   - Experience range
   - Education level
   - Pagination

5. Create unit tests (tests/test_candidate_search.py)
   - Test search with various criteria
   - Test pagination
   - Test empty results

6. Create integration tests
   - Search against database
```

### Acceptance Criteria
- [ ] Search by skills (exact match)
- [ ] Search by experience range
- [ ] Semantic skill matching
- [ ] Paginated results
- [ ] Sorting options
- [ ] Unit tests: 90%+ coverage
- [ ] Load test: <200ms for 10K records
- [ ] API documentation

### Estimated Effort: 8-12 hours

---

## Task 5: Match Results & History API

### Goal
Retrieve and manage match results.

### Requirements

**Endpoints:**
```
POST /api/matches - Create a match
  Body:
    {
      "candidate_id": int,
      "job_id": int
    }
  Response:
    {
      "match_id": str,
      "match_score": float,
      "candidate": {...},
      "job": {...},
      "gap_analysis": {...}
    }

GET /api/matches/{match_id} - Retrieve match details

DELETE /api/matches/{match_id} - Delete match record

GET /api/matches - List all matches
  Query params:
    - candidate_id: int
    - job_id: int
    - min_score: float
    - limit: int = 20

PUT /api/matches/{match_id}/status - Update match status
  Body: {"status": "rejected" | "shortlisted" | "interview"}
```

### Implementation Plan

```
1. Create match API routes
   - POST /api/matches (create)
   - GET /api/matches (list)
   - GET /api/matches/{id} (get)
   - DELETE /api/matches/{id}
   - PUT /api/matches/{id}/status

2. Create bedrock_poc/repositories/match_repo.py
   - Create, retrieve, update, delete matches
   - Database query optimization

3. Integrate with matching engine
   - Trigger matching on POST
   - Store results in database

4. Create Pydantic models for API

5. Create unit tests (tests/test_match_api.py)
   - Test CRUD operations
   - Test status updates
   - Test filtering

6. Create integration tests
```

### Acceptance Criteria
- [ ] Create matches via API
- [ ] Retrieve match history
- [ ] Update match status
- [ ] Delete old matches
- [ ] Filter by criteria
- [ ] Unit tests: 90%+ coverage
- [ ] API documentation
- [ ] Response time <500ms

### Estimated Effort: 8-12 hours

---

## Task 6: Test Coverage Expansion

### Goal
Achieve 80%+ test coverage across all new modules.

### Requirements

**Coverage Targets:**
- Unit tests: 95%+ for models and utilities
- Integration tests: 80%+ for API endpoints
- E2E tests: Key workflows
- Database tests: Schema and migrations

### Test Categories

```
1. Unit Tests
   - Job parser (parsing edge cases)
   - Matcher (scoring algorithm)
   - Gap analyzer (resource suggestions)
   - Models (validation)

2. Integration Tests
   - Parse job -> Search candidates -> Match -> Store
   - Database operations
   - API endpoints

3. E2E Tests
   - Streamlit: Parse resume, search, view matches
   - CLI: Parse job, run matching
   - API: Full workflow

4. Performance Tests
   - Parsing large documents (<5s)
   - Matching 1000 candidates (<10s)
   - API response time (<500ms)
```

### Implementation Plan

```
1. Review existing tests
2. Add missing unit tests
3. Add integration test suite
4. Add E2E test workflows
5. Generate coverage report: pytest --cov=bedrock_poc tests/
6. Target: 80%+ coverage
```

### Acceptance Criteria
- [ ] Overall coverage: 80%+
- [ ] No critical paths untested
- [ ] All APIs have endpoint tests
- [ ] Database operations tested
- [ ] Performance benchmarks defined
- [ ] CI/CD integration ready

### Estimated Effort: 10-14 hours

---

## Task 7: Documentation & API Specification

### Goal
Create comprehensive documentation for developers and API consumers.

### Documentation Components

```
1. API Documentation (OpenAPI/Swagger)
   - All endpoints
   - Request/response schemas
   - Error codes
   - Example requests

2. Architecture Documentation
   - System design diagrams
   - Data flow
   - Database schema
   - Integration points

3. Developer Guide
   - Local development setup
   - Adding new features
   - Testing procedures
   - Deployment steps

4. API Consumer Guide
   - Authentication (if needed)
   - Rate limits
   - Pagination
   - Error handling

5. Database Documentation
   - Schema details
   - Indexes
   - Performance considerations
   - Backup procedures
```

### Implementation Plan

```
1. Generate OpenAPI spec from FastAPI/Streamlit
2. Update README.md with latest features
3. Create API_DOCUMENTATION.md
4. Create DEVELOPER_GUIDE.md
5. Add docstrings to all functions
6. Create architecture diagrams
```

### Acceptance Criteria
- [ ] OpenAPI spec complete
- [ ] All endpoints documented
- [ ] Code examples included
- [ ] Data flow diagrams
- [ ] Deployment guide
- [ ] Troubleshooting section

### Estimated Effort: 6-10 hours

---

## Timeline & Milestones

### Week 1-2: Job Parser (12-16 hrs)
- [ ] Data model definition
- [ ] Parser implementation
- [ ] Database integration
- [ ] Unit tests
- [ ] Demo with sample jobs

### Week 2-3: Matching Engine (14-18 hrs)
- [ ] Matching algorithm
- [ ] Scoring system
- [ ] Database storage
- [ ] Unit & integration tests
- [ ] Performance optimization

### Week 3-4: Gap Analysis (10-14 hrs)
- [ ] Gap identification
- [ ] Learning resources
- [ ] Database storage
- [ ] Tests & documentation

### Week 4-5: Search & Match APIs (16-24 hrs)
- [ ] Candidate search API
- [ ] Match results API
- [ ] Full integration
- [ ] E2E testing

### Week 5-6: Testing & Docs (16-24 hrs)
- [ ] Test coverage expansion
- [ ] Documentation
- [ ] API specs
- [ ] Performance tuning

### Buffer: Week 6-7 (14 hrs)
- Bug fixes
- Performance optimization
- Deployment prep

---

## Success Metrics

| Metric | Target | Owner |
|--------|--------|-------|
| Test Coverage | 80%+ | Developer |
| API Response Time | <500ms | Developer |
| Parsing Accuracy | 90%+ | Developer |
| Match Score Correlation | 0.85+ | Developer |
| Documentation Complete | 100% | Developer |
| Zero Critical Bugs | 100% | QA |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Matching accuracy below target | Medium | High | Early testing with real data |
| PostgreSQL performance issues | Low | High | Query optimization, indexing |
| API scalability concerns | Medium | Medium | Load testing early |
| Scope creep | High | Medium | Strict change management |

---

## Resources Required

- 1-2 Python developers (senior level)
- PostgreSQL instance (local + staging)
- AWS Bedrock access
- Test data (job descriptions, resumes)
- Time: ~80-120 hours total

---

## Next Steps

1. ✅ Environment setup complete
2. ✅ Database configured
3. ✅ Tests passing
4. 📋 Begin Task 1: Job Parser (Week 1)
5. 📋 Daily status updates
6. 📋 Weekly progress reviews

---

**Status:** Ready to Begin Phase 2  
**Start Date:** 2026-08-10  
**Target Completion:** 2026-09-30  
**Owner:** Development Team  
**Last Updated:** 2026-08-10
