# Phase 2: Implementation Proposal & Action Plan

**Date:** September 3, 2026  
**Status:** PROPOSAL - AWAITING APPROVAL  
**Objective:** Implement async job queue to achieve 95%+ success rate at 15-20 concurrent users

---

## Overview

This proposal outlines the step-by-step implementation plan for Phase 2 asynchronous processing. Based on the architecture design, we'll transform the synchronous Bedrock API calls into a background job queue system.

---

## Why This Approach?

**Problem we're solving:**
- Current 80-83% success rate at 20 users
- HTTP connection pool exhaustion
- 20% failure rate due to connection resets, not timeouts

**Solution benefits:**
- ✅ Immediate user response (<100ms) → higher perceived performance
- ✅ Background processing → no connection pool blocking
- ✅ Automatic retry logic → recover from transient failures
- ✅ Scalable architecture → grow to 100+ users

---

## Implementation Breakdown

### Phase 2A: Infrastructure Setup (2 days)

**Step 1: Set up Redis**
```bash
# Development
docker run -d -p 6379:6379 redis:latest

# Or install locally
brew install redis
redis-server
```

**Step 2: Set up AWS SQS**
- Create queue: `bedrock-jobs-queue`
- Visibility timeout: 300 seconds
- Message retention: 24 hours

**Step 3: Install dependencies**
```bash
pip install celery redis boto3 celery-sqlalchemy
```

**Files to create:**
- `bedrock_poc/celery_app.py` - Celery configuration
- `bedrock_poc/config/async_config.py` - Async settings

### Phase 2B: Database & Schema (1 day)

**Step 1: Create job tracking table**
```python
# bedrock_poc/models.py - Add new model

class JobQueue(Base):
    __tablename__ = "job_queue"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    job_id = Column(String(36), unique=True)
    job_description = Column(Text)
    status = Column(String(20), default="pending")
    result = Column(JSON)
    retry_count = Column(Integer, default=0)
    error_message = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
```

**Step 2: Create migration**
```bash
alembic revision --autogenerate -m "Add job_queue table"
alembic upgrade head
```

**Files to modify:**
- `bedrock_poc/models.py` - Add JobQueue model
- `alembic/versions/` - New migration file

### Phase 2C: Celery Task Implementation (2 days)

**Step 1: Create async task**
```python
# bedrock_poc/tasks/parse_job.py

from celery import shared_task
from bedrock_poc.client import converse
from bedrock_poc.models import JobQueue

@shared_task(bind=True, max_retries=3)
def parse_job_description_async(self, job_id, job_description, user_id):
    """Parse job description asynchronously"""
    try:
        # Call Bedrock
        result = converse(
            client=bedrock_client,
            messages=[{"role": "user", "content": [{"text": job_description}]}],
            system_prompt=JOB_PARSING_PROMPT,
            max_tokens=1024
        )
        
        # Update database
        job = JobQueue.query.filter_by(job_id=job_id).first()
        job.status = "completed"
        job.result = result
        job.completed_at = datetime.utcnow()
        db.session.commit()
        
        return result
        
    except (TimeoutError, ConnectionError) as e:
        # Retry with exponential backoff
        retry_delay = 3 ** self.request.retries
        raise self.retry(exc=e, countdown=retry_delay, max_retries=3)
        
    except Exception as e:
        # Non-retryable error
        job = JobQueue.query.filter_by(job_id=job_id).first()
        job.status = "failed"
        job.error_message = str(e)
        db.session.commit()
        raise
```

**Files to create:**
- `bedrock_poc/tasks/parse_job.py` - Celery task
- `bedrock_poc/tasks/__init__.py` - Task package

**Files to modify:**
- `bedrock_poc/celery_app.py` - Task registration

### Phase 2D: API Endpoints (2 days)

**Step 1: Add async endpoint**
```python
# bedrock_poc/api/jobs.py - Add new route

@router.post("/jobs/parse-async")
async def parse_job_async(
    request: JobDescriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """Submit job for async parsing"""
    # Validate input
    if not request.job_description or len(request.job_description) < 10:
        raise HTTPException(status_code=400, detail="Invalid job description")
    
    # Create job record
    job = JobQueue(
        user_id=current_user.id,
        job_id=str(uuid.uuid4()),
        job_description=request.job_description,
        status="pending"
    )
    db.session.add(job)
    db.session.commit()
    
    # Queue async task
    parse_job_description_async.delay(
        job.job_id,
        request.job_description,
        current_user.id
    )
    
    return {
        "job_id": job.job_id,
        "status": "pending",
        "status_url": f"/api/jobs/{job.job_id}/status"
    }
```

**Step 2: Add status endpoint**
```python
@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get job status and results"""
    job = JobQueue.query.filter_by(job_id=job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    response = {
        "job_id": job.job_id,
        "status": job.status,
        "created_at": job.created_at
    }
    
    if job.status == "completed":
        response["result"] = job.result
    elif job.status == "failed":
        response["error"] = job.error_message
    
    return response
```

**Step 3: Keep sync endpoint (backward compatible)**
```python
@router.post("/jobs/parse")
async def parse_job_sync(request: JobDescriptionRequest, ...):
    """
    Original sync endpoint - now calls async internally
    Maintains backward compatibility
    """
    job_id = str(uuid.uuid4())
    
    # Submit async task
    task = parse_job_description_async.delay(
        job_id, request.job_description, current_user.id
    )
    
    # Wait for result (synchronously)
    result = task.get(timeout=120)
    
    return result
```

**Files to modify:**
- `bedrock_poc/api/jobs.py` - Add async and status endpoints

### Phase 2E: Testing (2-3 days)

**Step 1: Unit tests**
```python
# tests/test_async_jobs.py

def test_job_submission():
    """Test async job submission"""
    response = client.post("/api/jobs/parse-async", 
        json={"job_description": "Senior Developer needed..."})
    assert response.status_code == 202
    assert "job_id" in response.json()

def test_job_status():
    """Test job status tracking"""
    # Submit job
    sub_response = client.post("/api/jobs/parse-async", ...)
    job_id = sub_response.json()["job_id"]
    
    # Check status
    status_response = client.get(f"/api/jobs/{job_id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] in ["pending", "processing", "completed"]

def test_retry_logic():
    """Test exponential backoff retry"""
    # Mock Bedrock to fail initially
    with patch("bedrock_poc.client.converse", side_effect=[
        ConnectionError("Failed"),
        ConnectionError("Failed"),
        {"parsed_result": "success"}
    ]):
        result = parse_job_description_async(...)
        assert result["parsed_result"] == "success"
```

**Step 2: Integration tests**
```python
def test_end_to_end_async_flow():
    """Test complete async flow"""
    # Submit job
    # Wait for processing
    # Verify result in database
    # Check Redis cache
    pass

def test_concurrent_job_processing():
    """Test 20 concurrent jobs"""
    # Submit 20 jobs
    # Monitor queue
    # Verify all complete successfully
    # Check success rate > 95%
    pass
```

**Step 3: Load tests**
```python
# tests/load_test_async.py

def test_20_concurrent_users_async():
    """
    Load test: 20 concurrent users
    Target: 95%+ success rate
    """
    results = run_load_test(
        num_users=20,
        num_jobs_per_user=10,
        duration_seconds=300
    )
    
    assert results["success_rate"] > 0.95
    assert results["avg_latency"] < 1.0  # API response
    assert results["job_completion_time"] < 70  # Processing
```

**Files to create:**
- `tests/test_async_jobs.py` - Unit & integration tests
- `tests/load_test_async.py` - Load tests

### Phase 2F: Documentation (1 day)

**Step 1: Architecture documentation**
- Update API documentation
- Add async flow diagrams
- Document retry behavior

**Step 2: Deployment guide**
- How to deploy with Celery
- How to scale workers
- How to monitor jobs

**Step 3: Operational runbook**
- How to troubleshoot
- How to check queue depth
- How to handle failures

**Files to create:**
- `docs/ASYNC_ARCHITECTURE.md` - Technical overview
- `docs/DEPLOYMENT_ASYNC.md` - Deployment guide
- `docs/OPERATIONS.md` - Troubleshooting

---

## Dependencies to Add

```
# requirements.txt additions
celery==5.3.0
redis==5.0.0
celery-sqlalchemy==0.4.1
boto3==1.28.0
```

---

## Configuration Changes

```python
# .env additions
REDIS_URL=redis://localhost:6379/0
SQS_QUEUE_NAME=bedrock-jobs-queue
AWS_SQS_REGION=us-east-2
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
MAX_CONCURRENT_BEDROCK=10
JOB_TIMEOUT=120
CELERY_WORKERS=5
```

---

## Success Criteria

✅ All endpoints tested and working  
✅ 20 concurrent users achieve 95%+ success rate  
✅ Async response time < 100ms  
✅ Job completion time < 70 seconds  
✅ Retry logic working (80%+ recovery rate)  
✅ No data loss or corruption  
✅ Complete documentation  
✅ Production-ready deployment guide  

---

## Rollback Plan

If issues occur:
1. Keep sync endpoint as fallback (already implemented)
2. Disable async processing, use sync only
3. Roll back to commit `d3d3efc`
4. Investigate and fix issues
5. Re-test before retry

---

## Timeline Estimate

| Task | Duration | Start | End |
|------|----------|-------|-----|
| 2A: Infrastructure | 2 days | Day 1 | Day 2 |
| 2B: Database | 1 day | Day 3 | Day 3 |
| 2C: Celery | 2 days | Day 4-5 | Day 5 |
| 2D: API Endpoints | 2 days | Day 6-7 | Day 7 |
| 2E: Testing | 2-3 days | Day 8-10 | Day 10 |
| 2F: Documentation | 1 day | Day 11 | Day 11 |

**Total: 10-11 days** (aggressive schedule)

**Conservative: 14-15 days** (with buffer for issues)

---

## Questions for Approval

1. ✅ **Architecture:** Does the SQS + Celery + Redis approach align with your infrastructure?
2. ✅ **Timeline:** Is 10-15 days acceptable for full implementation?
3. ✅ **Backward Compatibility:** Keep sync endpoint as fallback?
4. ✅ **Scaling:** Should we design for 100+ users from the start?
5. ✅ **Monitoring:** What alerting/monitoring do you need?

---

## Next Steps (If Approved)

1. ✅ Review and approve this proposal
2. ⏳ Approve architecture design
3. ⏳ Start Phase 2A (Infrastructure)
4. ⏳ Daily status updates

---

**Status:** AWAITING APPROVAL  
**Prepared by:** Claude Code Assistant  
**Date:** September 3, 2026

