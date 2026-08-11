# AI Recruiter Assistant - Phase 1 Implementation Plan

**Project:** AI Recruiter Assistant  
**Phase:** 1 (MVP)  
**Status:** 📋 Planning  
**Estimated Duration:** 4-6 weeks

---

## **PHASE 1: CORE FEATURES**

### **Feature Breakdown**

```
Phase 1 Scope:
├── Resume Parsing & Profile Extraction
├── Candidate Profile Management (CRUD)
├── Job Description Parsing
├── Resume-to-JD Matching & Scoring
├── Candidate Search & Filtering
├── Backend REST APIs
├── Database Schema
└── React UI (Basic)
```

---

## **ARCHITECTURE OVERVIEW**

```
┌─────────────────────────────────────┐
│     React Frontend (UI)             │
│  - Resume Upload                    │
│  - Candidate Management             │
│  - Job Posting                      │
│  - Match Results Viewer             │
└────────────────┬────────────────────┘
                 │ (REST APIs)
                 ↓
┌─────────────────────────────────────┐
│   FastAPI/Django Backend            │
│  - Resume Parser API                │
│  - Candidate APIs (CRUD)            │
│  - Job Description Parser API       │
│  - Matching Engine API              │
│  - Search & Filter API              │
└────────────────┬────────────────────┘
                 │ (SQL)
                 ↓
┌─────────────────────────────────────┐
│     PostgreSQL Database             │
│  - candidates table                 │
│  - job_descriptions table           │
│  - matches table                    │
│  - search_index table               │
└─────────────────────────────────────┘
                 │ (API calls)
                 ↓
┌─────────────────────────────────────┐
│     AWS Bedrock (Claude + Embeddings)
│  - Resume/JD parsing (Claude)       │
│  - Semantic matching (Embeddings)   │
└─────────────────────────────────────┘
```

---

## **TECHNOLOGY STACK**

### **Backend**

| Component | Technology | Reason |
|-----------|-----------|--------|
| Framework | FastAPI (Python) | Fast, modern, async-ready |
| Database | PostgreSQL | Robust, JSON support, full-text search |
| ORM | SQLAlchemy | Powerful, flexible, well-maintained |
| API Docs | Swagger/OpenAPI | Auto-generated, interactive |
| AI/ML | AWS Bedrock | Claude for parsing, Embeddings for matching |

### **Frontend**

| Component | Technology | Reason |
|-----------|-----------|--------|
| Framework | React 18 | Component-based, large ecosystem |
| State | Redux/Zustand | Predictable state management |
| Styling | Tailwind CSS | Utility-first, responsive |
| File Upload | Dropzone.js | Drag-and-drop support |
| Tables | React Table | Flexible data tables |
| Charts | Recharts | Interactive visualizations |

### **Infrastructure**

| Component | Technology | Reason |
|-----------|-----------|--------|
| Backend Server | EC2 (existing) | Familiar, already configured |
| Database | RDS PostgreSQL | Managed, automated backups |
| File Storage | S3 | Scalable, durable |
| Container | Docker | Deployment consistency |

---

## **DATABASE SCHEMA**

### **Core Tables**

#### **1. candidates**
```sql
CREATE TABLE candidates (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    full_name VARCHAR(255) NOT NULL,
    
    -- Parsed profile data
    skills TEXT[],
    experience_years INTEGER,
    current_title VARCHAR(255),
    current_company VARCHAR(255),
    
    -- Structured data from resume
    profile_json JSONB,  -- Full parsed profile
    
    -- File references
    resume_file_path VARCHAR(512),
    resume_s3_key VARCHAR(512),
    
    -- Status & metadata
    status VARCHAR(50),  -- active, archived, etc
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Search optimization
    full_text_search tsvector,
    embedding vector(1536)  -- Titan embeddings
);
```

#### **2. job_descriptions**
```sql
CREATE TABLE job_descriptions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    
    -- Parsed JD data
    required_skills TEXT[],
    nice_to_have_skills TEXT[],
    experience_required INTEGER,  -- years
    job_type VARCHAR(50),  -- full-time, contract, etc
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    
    -- Structured data from JD
    job_details_json JSONB,
    
    -- Full text content
    description TEXT,
    
    -- Status
    status VARCHAR(50),  -- open, closed, etc
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Search optimization
    full_text_search tsvector,
    embedding vector(1536)  -- Titan embeddings
);
```

#### **3. matches**
```sql
CREATE TABLE matches (
    id UUID PRIMARY KEY,
    candidate_id UUID NOT NULL REFERENCES candidates(id),
    job_id UUID NOT NULL REFERENCES job_descriptions(id),
    
    -- Match scores (0-100)
    skills_match NUMERIC(5,2),
    experience_match NUMERIC(5,2),
    overall_score NUMERIC(5,2),
    
    -- Matching details
    matched_skills TEXT[],
    missing_skills TEXT[],
    match_explanation TEXT,
    match_details_json JSONB,
    
    -- Recommendation
    recommendation VARCHAR(50),  -- recommended, marginal, not_recommended
    
    -- Status
    created_at TIMESTAMP DEFAULT NOW(),
    viewed_at TIMESTAMP,
    status VARCHAR(50),  -- pending, contacted, hired, etc
    
    UNIQUE(candidate_id, job_id)
);
```

#### **4. search_filters**
```sql
CREATE TABLE search_filters (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    filter_name VARCHAR(255),
    
    -- Filter criteria
    skills_required TEXT[],
    min_experience INTEGER,
    job_types TEXT[],
    salary_range_min DECIMAL(10,2),
    salary_range_max DECIMAL(10,2),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### **5. users** (if not existing)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    company_name VARCHAR(255),
    role VARCHAR(50),  -- recruiter, admin, etc
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## **API ENDPOINTS (REST)**

### **Candidate Management**

```
POST   /api/v1/candidates/upload          → Upload & parse resume
GET    /api/v1/candidates                 → List all candidates
GET    /api/v1/candidates/{id}            → Get candidate details
PUT    /api/v1/candidates/{id}            → Update candidate
DELETE /api/v1/candidates/{id}            → Delete candidate
GET    /api/v1/candidates/search          → Search candidates
```

### **Job Descriptions**

```
POST   /api/v1/jobs/create                → Create & parse JD
GET    /api/v1/jobs                       → List all jobs
GET    /api/v1/jobs/{id}                  → Get JD details
PUT    /api/v1/jobs/{id}                  → Update JD
DELETE /api/v1/jobs/{id}                  → Delete JD
```

### **Matching Engine**

```
POST   /api/v1/matches/calculate          → Calculate matches for job
GET    /api/v1/matches/job/{id}           → Get matches for a job
GET    /api/v1/matches/candidate/{id}     → Get matches for candidate
GET    /api/v1/matches/{id}               → Get match details
PUT    /api/v1/matches/{id}/status        → Update match status
```

### **Search & Filtering**

```
POST   /api/v1/search/candidates          → Advanced search
POST   /api/v1/search/save-filter         → Save search filter
GET    /api/v1/search/filters             → List saved filters
```

---

## **PHASE 1 DELIVERABLES**

### **Backend Components**

```
ai-recruiter-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 (FastAPI app)
│   ├── config.py               (Configuration)
│   ├── database.py             (DB connection)
│   │
│   ├── models/                 (SQLAlchemy models)
│   │   ├── candidate.py
│   │   ├── job.py
│   │   ├── match.py
│   │   └── user.py
│   │
│   ├── schemas/                (Pydantic schemas - validation)
│   │   ├── candidate.py
│   │   ├── job.py
│   │   ├── match.py
│   │   └── resume_parsed.py
│   │
│   ├── api/                    (REST API endpoints)
│   │   ├── candidates.py
│   │   ├── jobs.py
│   │   ├── matches.py
│   │   ├── search.py
│   │   └── health.py
│   │
│   ├── services/               (Business logic)
│   │   ├── resume_parser.py    (Uses Bedrock Claude)
│   │   ├── jd_parser.py        (Uses Bedrock Claude)
│   │   ├── matching_engine.py  (Uses Bedrock Embeddings)
│   │   └── search_service.py
│   │
│   ├── utils/
│   │   ├── file_handler.py
│   │   ├── embedding.py
│   │   └── constants.py
│   │
│   └── migrations/             (Alembic DB migrations)
│
├── requirements.txt
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

### **Frontend Components**

```
ai-recruiter-frontend/
├── src/
│   ├── components/
│   │   ├── ResumeUpload.jsx
│   │   ├── CandidateList.jsx
│   │   ├── CandidateDetail.jsx
│   │   ├── JobForm.jsx
│   │   ├── MatchResults.jsx
│   │   ├── SearchFilter.jsx
│   │   └── Dashboard.jsx
│   │
│   ├── pages/
│   │   ├── Candidates.jsx
│   │   ├── Jobs.jsx
│   │   ├── Matches.jsx
│   │   └── Dashboard.jsx
│   │
│   ├── services/
│   │   ├── api.js             (API client)
│   │   └── auth.js
│   │
│   ├── store/
│   │   ├── candidateSlice.js
│   │   ├── jobSlice.js
│   │   └── matchSlice.js
│   │
│   ├── App.jsx
│   └── index.jsx
│
├── package.json
└── tailwind.config.js
```

---

## **PHASE 1 IMPLEMENTATION ROADMAP**

### **Week 1: Backend Setup & Database**

- [ ] Day 1-2: Project setup, FastAPI structure, DB schema
- [ ] Day 3-4: SQLAlchemy models, Alembic migrations
- [ ] Day 5: Database connection, Docker setup

### **Week 2: Resume & JD Parsing**

- [ ] Day 1-2: Resume parser service (using Bedrock Claude)
- [ ] Day 3-4: JD parser service (using Bedrock Claude)
- [ ] Day 5: Test parsing with sample files

### **Week 3: Candidate & Job APIs**

- [ ] Day 1-2: Candidate CRUD endpoints
- [ ] Day 3-4: Job description CRUD endpoints
- [ ] Day 5: Input validation, error handling

### **Week 4: Matching Engine & Search**

- [ ] Day 1-2: Matching algorithm using embeddings
- [ ] Day 3-4: Search & filtering logic
- [ ] Day 5: Match scoring refinement

### **Week 5: Frontend - React UI**

- [ ] Day 1-2: Resume upload component
- [ ] Day 3-4: Candidate management UI
- [ ] Day 5: Match results viewer

### **Week 6: Integration & Testing**

- [ ] Day 1-2: Frontend-backend integration
- [ ] Day 3-4: End-to-end testing
- [ ] Day 5: Bug fixes, documentation

---

## **KEY TECHNOLOGIES TO INTEGRATE**

### **AWS Bedrock Usage**

**1. Resume Parsing**
```python
# Claude 3.5 Sonnet for structured extraction
prompt = """
Parse this resume and extract:
- Full name, email, phone
- Skills (as list)
- Work experience (company, title, dates, description)
- Education (degree, school, year)
- Certifications
- Languages

Return as JSON.
"""
```

**2. JD Parsing**
```python
# Same model for consistency
prompt = """
Parse this job description and extract:
- Job title
- Required skills (as list)
- Nice-to-have skills
- Years of experience required
- Job type (full-time, contract, etc)
- Salary range
- Responsibilities

Return as JSON.
"""
```

**3. Semantic Matching**
```python
# Titan Embeddings for similarity matching
1. Embed candidate skills
2. Embed job required skills
3. Calculate cosine similarity
4. Score: (matched_count / total_required) * 100
```

---

## **DATABASE INDEXES & OPTIMIZATION**

```sql
-- Speed up searches
CREATE INDEX idx_candidates_email ON candidates(email);
CREATE INDEX idx_candidates_status ON candidates(status);
CREATE INDEX idx_jobs_status ON job_descriptions(status);
CREATE INDEX idx_matches_candidate_id ON matches(candidate_id);
CREATE INDEX idx_matches_job_id ON matches(job_id);

-- Full-text search
CREATE INDEX idx_candidates_fts ON candidates USING GIN(full_text_search);
CREATE INDEX idx_jobs_fts ON job_descriptions USING GIN(full_text_search);

-- Vector similarity search (for embeddings)
CREATE INDEX idx_candidates_embedding ON candidates USING ivfflat(embedding vector_cosine_ops);
CREATE INDEX idx_jobs_embedding ON job_descriptions USING ivfflat(embedding vector_cosine_ops);
```

---

## **SAMPLE DATA FOR TESTING**

```json
{
  "candidate": {
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "555-1234",
    "skills": ["Python", "AWS", "Machine Learning"],
    "experience_years": 5,
    "current_title": "Senior ML Engineer",
    "current_company": "Tech Corp"
  },
  "job": {
    "title": "ML Engineer",
    "company": "AI Startup",
    "required_skills": ["Python", "AWS", "Deep Learning"],
    "experience_required": 3,
    "job_type": "full-time"
  },
  "expected_match": {
    "overall_score": 85,
    "matched_skills": ["Python", "AWS"],
    "missing_skills": ["Deep Learning"],
    "recommendation": "recommended"
  }
}
```

---

## **DEPLOYMENT PLAN**

### **Phase 1 Deployment**

1. **Backend**: Deploy to EC2 (with Docker)
2. **Database**: RDS PostgreSQL
3. **Frontend**: S3 + CloudFront (or EC2)
4. **File Storage**: S3 for resumes/JDs
5. **API Gateway**: Optional (API management)

### **Environment Configuration**

```bash
# .env variables
DATABASE_URL=postgresql://user:pass@rds-endpoint/dbname
AWS_BEDROCK_REGION=us-east-1
AWS_S3_BUCKET=recruiter-files
JWT_SECRET=your-secret
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

---

## **SUCCESS METRICS - PHASE 1**

- ✅ Upload & parse 10+ resumes (accuracy > 90%)
- ✅ Parse 5+ job descriptions
- ✅ Generate matches with scoring (0-100)
- ✅ Search/filter returns correct results
- ✅ All APIs documented in Swagger
- ✅ Basic UI fully functional
- ✅ < 5 second API response time
- ✅ Database can handle 1000+ candidates/jobs

---

## **PHASE 2+ ROADMAP (Future)**

```
Phase 2:
├── Advanced matching (skills gap analysis)
├── Candidate rank by best fit
├── Bulk operations (import 100s of candidates)
└── Email notifications

Phase 3:
├── Interview scheduling
├── Resume similarity detection (duplicate detection)
├── Analytics dashboard
└── Candidate feedback collection

Phase 4:
├── ML model training (improve matching)
├── Skill assessment integration
├── ATS integration (LinkedIn, Indeed)
└── GDPR/data privacy compliance
```

---

## **ESTIMATED EFFORT**

| Component | Effort | Time |
|-----------|--------|------|
| Backend Setup | Medium | 2 days |
| Database Design | Medium | 1 day |
| Parsing Services | High | 4 days |
| Matching Engine | High | 4 days |
| API Endpoints | Medium | 3 days |
| Frontend UI | Medium | 5 days |
| Integration/Testing | Medium | 3 days |
| Documentation | Low | 2 days |
| **TOTAL** | | **4-6 weeks** |

---

## **RISKS & MITIGATION**

| Risk | Impact | Mitigation |
|------|--------|------------|
| Bedrock API rate limits | High | Implement caching, queue management |
| Resume format variations | High | Handle PDF, DOCX, TXT; test with 50+ samples |
| Matching accuracy | Medium | Refine prompts, validate with domain experts |
| DB performance at scale | Medium | Add indexes, implement pagination |
| Frontend complexity | Medium | Use component library, start simple |

---

## **NEXT STEPS**

1. ✅ Approve Phase 1 scope
2. ✅ Set up Git repository for new project
3. ✅ Create development environment (local + staging)
4. ✅ Create detailed API specification
5. ✅ Start Week 1 implementation

---

**Ready to start Phase 1 implementation?** 

Which component should we build first?
- [ ] Backend (FastAPI + PostgreSQL)
- [ ] Database (schema + migrations)
- [ ] Parsing services (Resume + JD)
- [ ] All of the above (parallel)

