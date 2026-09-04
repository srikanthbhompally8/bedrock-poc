# Phase 2: Asynchronous Processing Architecture Design

**Date:** September 3, 2026  
**Phase:** 2 - Concurrency Optimization (Moderate Strategy)  
**Target:** 15-20 concurrent users with 95%+ success rate  
**Status:** DESIGN PHASE - AWAITING APPROVAL

---

## Executive Summary

Replace synchronous Bedrock API calls with asynchronous job queue processing using **AWS SQS + Celery + Redis**. This decouples user-facing API requests from long-running AI processing, enabling higher concurrency and reliability.

**Key Benefits:**
- ✅ Increase success rate from 80-83% → 95%+
- ✅ Support 15-20 concurrent users reliably
- ✅ Reduce visible latency (async responses in <1s)
- ✅ Automatic retry logic for failed jobs
- ✅ Scalable to 100+ users with worker pool expansion

---

## Current Architecture Problem

**Synchronous Flow:**
```
User Request → FastAPI → Bedrock API (30-62s wait) → Response
                              ↓
                    Connection pool exhaustion
                    20% failure rate at 20 users
```

**Issue:** Bedrock API calls block HTTP connection. Under load:
- Connection pool exhausted after ~15-20 concurrent requests
- Remaining requests fail with connection errors
- No retry/recovery mechanism

---

## Proposed Asynchronous Architecture

**New Flow:**
```
User Request → FastAPI (validation, queue job) → Immediate response (202 Accepted)
                              ↓
                        SQS Job Queue
                              ↓
                    Celery Worker Pool
                              ↓
                    Bedrock API (30-62s) → Process result
                              ↓
                    Redis Cache (store result)
                              ↓
        User polls `/api/jobs/{job_id}/status` for result
```

**Benefits:**
- User gets immediate response (< 100ms)
- Long-running task isolated from HTTP layer
- Automatic retry with exponential backoff
- Multiple workers can process jobs in parallel
- Failed jobs don't block other users

---

## Technology Stack

### Message Queue: AWS SQS
```
Why: AWS-native, managed, reliable, integrates with existing setup
Config:
  - Queue name: bedrock-jobs-queue
  - Visibility timeout: 300s (5 minutes)
  - Message retention: 86400s (24 hours)
  - Batch size: 10 messages
```

### Job Worker: Celery + Redis
```
Why: Industry standard, supports retries, easy scaling
Config:
  - Broker: Redis (local for dev, ElastiCache for prod)
  - Result backend: Redis
  - Concurrency: 5-10 workers per instance
  - Retry: exponential backoff (3s, 9s, 27s)
  - Max retries: 3 for transient errors
```

### Caching: Redis
```
Why: Fast, in-memory, supports TTL
Config:
  - Store job results (24hr TTL)
  - Cache Bedrock responses (optional)
  - Job status tracking
```

---

## Implementation Components

### 1. Database Schema Changes
```python
# New table: job_queue
- id (PK)
- user_id (FK)
- job_id (unique, celery task ID)
- job_description (text)
- status (pending/processing/completed/failed)
- result (JSON, parsed job data)
- created_at
- completed_at
- retry_count
- error_message
```

### 2. New API Endpoints

**Submit Job (Async)**
```
POST /api/jobs/parse-async
Request: { "job_description": "..." }
Response: { 
  "job_id": "uuid",
  "status": "pending",
  "status_url": "/api/jobs/{job_id}/status"
}
Status: 202 Accepted
```

**Check Status**
```
GET /api/jobs/{job_id}/status
Response: {
  "job_id": "uuid",
  "status": "processing" | "completed" | "failed",
  "result": {...} (if completed),
  "error": "..." (if failed)
}
Status: 200 OK
```

**Keep Backward Compatibility**
```
POST /api/jobs/parse (existing sync endpoint)
Internally: Submit to queue, wait for result, return
Status: 200 OK (unchanged behavior)
```

### 3. Celery Task Definition

```python
# bedrock_poc/tasks/parse_job.py

@celery_app.task(bind=True, max_retries=3)
def parse_job_description(self, job_id, job_description):
    """
    Async task: Parse job description via Bedrock
    Retry on transient errors with exponential backoff
    """
    try:
        # Call Bedrock API
        result = call_bedrock_api(job_description)
        
        # Store result in Redis
        cache.set(f"job:{job_id}", result, ttl=86400)
        
        # Update database
        Job.update(job_id, status="completed", result=result)
        
        return result
        
    except TransientError as e:
        # Retry with backoff: 3s, 9s, 27s
        raise self.retry(exc=e, countdown=3**self.request.retries)
        
    except Exception as e:
        # Fatal error, don't retry
        Job.update(job_id, status="failed", error=str(e))
        raise
```

### 4. Request Queuing & Concurrency Limits

```python
# bedrock_poc/middleware/concurrency.py

class ConcurrencyLimiter:
    """
    Limits concurrent Bedrock requests
    Queue excess requests instead of failing
    """
    def __init__(self, max_concurrent=10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue = asyncio.Queue()
    
    async def acquire(self):
        await self.semaphore.acquire()
    
    async def release(self):
        self.semaphore.release()
```

---

## Retry Logic Details

**Exponential Backoff Strategy:**
```
Attempt 1: Immediate
Attempt 2: Wait 3 seconds
Attempt 3: Wait 9 seconds
Attempt 4: Wait 27 seconds
Max total time: ~40 seconds

Retryable errors:
  - 429 (Throttling)
  - 504 (Gateway timeout)
  - Connection timeouts
  - Transient network errors

Non-retryable errors:
  - 400 (Validation)
  - 401 (Authentication)
  - 403 (Forbidden)
```

---

## Deployment Architecture

### Development (Single Server)
```
FastAPI Server (8000)
├── Redis (6379)
├── SQS Queue (AWS)
└── Celery Worker (background)
```

### Production (Scalable)
```
Load Balancer
├── FastAPI Server 1 (8000)
├── FastAPI Server 2 (8000)
├── FastAPI Server N (8000)
    ↓
AWS SQS Queue (bedrock-jobs)
    ↓
Celery Worker Pool (auto-scaling)
├── Worker 1
├── Worker 2
├── Worker N
    ↓
Redis Cluster (ElastiCache)
    ↓
RDS PostgreSQL
```

---

## Success Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|---|
| Success Rate (20 users) | 80-83% | 95%+ | Performance test |
| User-facing latency | 31-35s | <100ms | API response time |
| Job completion time | N/A | 31-40s | Celery task duration |
| Retry success rate | N/A | 80%+ | Job completion logs |
| System stability | No cascades | Sustained | 60min stress test |

---

## Implementation Timeline

| Phase | Duration | Deliverable |
|-------|----------|---|
| Setup | 1-2 days | Redis, SQS, Celery configured |
| Core | 2-3 days | Async endpoints, job tracking |
| Testing | 2-3 days | Unit, integration, load tests |
| Validation | 1 day | 95% success rate confirmed |
| Documentation | 1 day | Architecture, deployment guide |

**Total: 7-10 days**

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|---|
| Redis single point of failure | Medium | Use Redis Cluster in prod |
| SQS queue overflow | Medium | Auto-scale worker pool |
| Long job queue delays | Medium | Monitor queue depth, adjust workers |
| Backward compatibility break | High | Keep sync endpoint as fallback |
| Bedrock API still slow | Low | Already handled by async model |

---

## Testing Strategy

### Unit Tests
- Job submission validation
- Retry logic behavior
- Error handling
- Result caching

### Integration Tests
- End-to-end async flow
- Queue processing
- Database updates
- Redis caching

### Load Tests
- 20 concurrent users with 95%+ success rate
- 100 concurrent users (queued behavior)
- Retry effectiveness
- Failure recovery

---

## Configuration Management

```python
# bedrock_poc/config.py

ASYNC_CONFIG = {
    "sqs_queue": "bedrock-jobs-queue",
    "max_concurrent_bedrock": 10,
    "job_timeout": 120,  # seconds
    "retry_backoff": [3, 9, 27],  # seconds
    "max_retries": 3,
    "celery_workers": 5,
    "result_ttl": 86400,  # 24 hours
}
```

All configurable via environment variables for dev/staging/prod.

---

## Database Migrations

```sql
-- New table for job tracking
CREATE TABLE job_queue (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    job_id VARCHAR(36) UNIQUE NOT NULL,
    job_description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    result JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_job_id (job_id)
);
```

---

## Next Steps (If Approved)

1. ✅ Review & approve this design
2. ⏳ Set up Redis and SQS in development
3. ⏳ Implement Celery task and async endpoints
4. ⏳ Write comprehensive tests
5. ⏳ Run load tests to validate 95% success rate
6. ⏳ Update documentation and deployment guides

---

**Design Status:** COMPLETE - AWAITING APPROVAL  
**Prepared by:** Claude Code Assistant  
**Date:** September 3, 2026

