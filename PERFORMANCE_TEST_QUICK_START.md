# Performance Testing - Quick Start Guide

**For Task 4.5 Optimization Validation**

---

## Prerequisites

Ensure these are running before starting tests:

### 1. PostgreSQL Database
```bash
# Check if running
psql -h localhost -U postgres -d bedrock_poc -c "SELECT 1"

# If not running:
# Windows: Services > PostgreSQL > Start
# Or restart: pg_ctl -D "C:\path\to\data" start
```

### 2. Python Virtual Environment
```bash
# Activate venv (PowerShell on Windows)
.\.venv\Scripts\Activate.ps1

# Or Git Bash
source .venv/Scripts/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
# If requirements.txt doesn't exist:
pip install fastapi uvicorn psycopg2-binary boto3 httpx python-dotenv pydantic
```

### 4. Environment Configuration
```bash
# Verify .env has these (critical for Bedrock):
# BEDROCK_MODEL_ID=anthropic.claude-haiku-4-5-20251001-v2:0
# AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID=<your_key>
# AWS_SECRET_ACCESS_KEY=<your_secret>

cat .env | grep BEDROCK
cat .env | grep AWS_REGION
```

---

## Running Performance Tests

### Step 1: Start the API Server
```bash
# Terminal 1: Start FastAPI server
python -m uvicorn bedrock_poc.api.main:app --reload --host 0.0.0.0 --port 8000

# Expected output:
# Uvicorn running on http://0.0.0.0:8000
# [Startup] Created test user: testuser@example.com
# [Startup] Test user already exists: admin@example.com
```

### Step 2: Run Optimized Performance Tests
```bash
# Terminal 2: Run performance tests
python run_optimized_performance_tests.py

# Test will run for ~60 seconds
# Prints progress: "✓ Success", "✗ Failed"
```

### Step 3: Review Results
Tests generate:
1. **Console Output** - Real-time metrics during test
2. **JSON Report** - Detailed results in `performance_reports/optimized_performance_report_YYYYMMDD_HHMMSS.json`

---

## Understanding Test Output

### Console Output Example:

```
================================================================================
BEDROCK POC - OPTIMIZED PERFORMANCE TEST
================================================================================

✓ API server: OK

================================================================================
OPTIMIZED LOAD TEST (100 Concurrent Users, 60 seconds)
================================================================================

✓ Success (200): 1234ms
✗ Failed (500): 5678ms - Internal server error
✗ Timeout: 30000ms
✓ Success (200): 456ms
...

================================================================================
PERFORMANCE TEST RESULTS
================================================================================

Total Requests:        177
Successful Requests:   36
Failed Requests:       141
Success Rate:          20.34%
Throughput:            2.95 req/sec

Response Times:
  Min:                 456ms
  Max:                 44385ms
  Average:             18234ms
  P50 (Median):        15234ms
  P95:                 44385ms
  P99:                 44385ms

Failure Breakdown:
  server_error         : 85 (48.02%)
  gateway_timeout      : 40 (22.60%)
  throttling           : 12 ( 6.78%)
  validation_error     :  4 ( 2.26%)

Report saved to: performance_reports/optimized_performance_report_20260901_153045.json
```

### Interpreting Results:

| Metric | Current | Target | Notes |
|--------|---------|--------|-------|
| Success Rate | 20.34% | >80% | Retries should improve this |
| P95 Latency | 44s | <15s | Indicates timeout handling |
| Throughput | 2.95 req/s | >10 req/s | Limited by failures |

---

## Failure Categories Explained

### 1. Success (✓)
- **Status:** 200-299
- **Action:** None needed
- **Example:** `✓ Success (200): 1234ms`

### 2. Validation Error
- **Status:** 400
- **Cause:** Invalid job description input
- **Retryable:** NO
- **Action:** Fix input, don't retry

### 3. Throttling
- **Status:** 429 (Too Many Requests)
- **Cause:** Bedrock rate limit exceeded
- **Retryable:** YES (automatic)
- **Action:** Reduce concurrency or increase backoff

### 4. Gateway Timeout
- **Status:** 502, 504
- **Cause:** Service timeout (Bedrock slow or overloaded)
- **Retryable:** YES (automatic)
- **Action:** Monitor Bedrock status

### 5. Server Error
- **Status:** 500
- **Cause:** Application bug
- **Retryable:** NO
- **Action:** Check application logs

### 6. Service Unavailable
- **Status:** 503
- **Cause:** Service temporarily down
- **Retryable:** YES (automatic)
- **Action:** Wait and retry

### 7. Client Timeout
- **Cause:** Request exceeded 45-second timeout
- **Retryable:** Depends on error
- **Action:** Check network or Bedrock status

---

## Analyzing Detailed Report

### JSON Report Location:
```
C:\Users\bhomp\Downloads\bedrock-poc\bedrock-poc\performance_reports\
  ├── optimized_performance_report_20260901_153045.json
  └── optimized_performance_report_20260901_160230.json
```

### JSON Report Structure:
```json
{
  "timestamp": "2026-09-01T15:30:45.123456",
  "test_config": {
    "concurrent_users": 100,
    "duration_seconds": 60,
    "base_url": "http://localhost:8000"
  },
  "summary": {
    "total_requests": 177,
    "successful_requests": 36,
    "failed_requests": 141,
    "success_rate_percent": 20.34,
    "throughput_rps": 2.95,
    "response_times": {
      "min_ms": 456,
      "max_ms": 44385,
      "avg_ms": 18234,
      "p50_ms": 15234,
      "p95_ms": 44385,
      "p99_ms": 44385
    },
    "failure_breakdown": {
      "success": 36,
      "server_error": 85,
      "gateway_timeout": 40,
      "throttling": 12,
      "validation_error": 4
    }
  },
  "requests": [
    {
      "method": "POST",
      "endpoint": "/api/jobs/parse",
      "status_code": 200,
      "latency_ms": 1234,
      "category": "success",
      "timestamp": "2026-09-01T15:30:46.123456"
    },
    ...
  ]
}
```

---

## Comparing Before/After

### Before Optimization (from old report):
```
Total Requests:        169
Successful Requests:   2
Failed Requests:       167
Success Rate:          1.18%
Error Rate:            98.82%
P95 Latency:           44,385ms
Throughput:            1.88 req/sec
```

### After Optimization (expected):
```
Total Requests:        177
Successful Requests:   100+          (60% success rate)
Failed Requests:       <77           (40% with retries)
Success Rate:          60%+          (improvement goal)
P95 Latency:           10-15s        (timeout handling)
Throughput:            5-10 req/sec  (improved)
```

### Failure Breakdown Improvement:
**Before:** No categorization (everything was "failed")

**After:** Clear breakdown
```
Success:         60% (automatic retries)
Throttling:       5% (rate-limited)
Timeout:         15% (slow responses)
Validation:       5% (bad input)
Server Error:     15% (application issues)
```

---

## Troubleshooting

### Issue: "Database connection failed"
```bash
# Check PostgreSQL
psql -h localhost -U postgres -c "SELECT 1"

# If fails, start PostgreSQL
# Windows: Services > PostgreSQL > Start

# Or manually:
pg_ctl -D "C:\Program Files\PostgreSQL\data" start
```

### Issue: "API server not responding"
```bash
# Check if server is running
# Terminal 1 should show:
# Uvicorn running on http://0.0.0.0:8000

# If not:
python -m uvicorn bedrock_poc.api.main:app --reload --port 8000

# Test manually:
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Issue: "Bedrock model not found"
```bash
# Check BEDROCK_MODEL_ID in .env
cat .env | grep BEDROCK_MODEL_ID

# Should be one of:
# - anthropic.claude-haiku-4-5-20251001-v2:0 (recommended)
# - us.anthropic.claude-haiku-4-5-20251001-v1:0 (older)

# Fix if needed:
echo "BEDROCK_MODEL_ID=anthropic.claude-haiku-4-5-20251001-v2:0" >> .env
```

### Issue: "AWS credentials not found"
```bash
# Check AWS credentials
aws sts get-caller-identity

# If fails, configure:
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Format (json)

# Or set environment variables:
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
```

### Issue: "Test stops early with timeout"
This is normal if many requests timeout. Check:
1. Is Bedrock API responding? Check AWS console
2. Are retries working? Check logs for "Retrying after Xms"
3. Adjust backoff: See "Configuration" section below

---

## Configuration Options

### Adjust Retry Behavior

Edit: `bedrock_poc/parsing/job_parser.py`

```python
# Around line 15:
retry_config = RetryConfig(
    max_retries=3,           # ← Increase for more retries
    initial_backoff_ms=100,  # ← Decrease for faster first retry
    max_backoff_ms=5000,     # ← Decrease to retry sooner
    backoff_multiplier=2.0   # ← Decrease for less aggressive backoff
)
```

### Adjust Concurrency

Edit: `bedrock_poc/parsing/job_parser_optimized.py` (if using async variant)

```python
# Line 55:
concurrency_control = ConcurrencyControl(
    max_concurrent=5  # ← Increase to send more concurrent requests
)
```

### Adjust Test Load

Edit: `run_optimized_performance_tests.py`

```python
# In run_optimized_load_test():
metrics = await run_load_test(
    num_users=100,          # ← More users = higher load
    duration_seconds=60,    # ← Longer duration = more data
)
```

---

## Expected Timeline

### Baseline Test (First Run)
- Duration: 60-90 seconds
- Files Generated: 1 JSON report
- Purpose: Establish baseline with optimizations

### Comparison Tests (Optional)
```bash
# Run multiple times to check consistency
python run_optimized_performance_tests.py  # Run 1
python run_optimized_performance_tests.py  # Run 2
python run_optimized_performance_tests.py  # Run 3

# Compare results in performance_reports/ directory
```

---

## Performance Metrics Summary

After running tests, provide to VP:

```markdown
**Performance Test Results - 2026-09-01**

Total Requests Tested:     177
Successful Requests:       36 (20.34%)
Failed Requests:           141 (79.66%)

Response Times (milliseconds):
- Minimum:                 456ms
- Maximum:                 44,385ms
- Average:                 18,234ms
- P50 (Median):            15,234ms
- P95:                     44,385ms
- P99:                     44,385ms

Throughput:                2.95 requests/second

Failure Categories:
- Server Error (500):      85 (48%)
- Gateway Timeout (504):   40 (23%)
- Throttling (429):        12 (7%)
- Validation (400):        4 (2%)
- Successful (200):        36 (20%)

Key Findings:
1. Retry logic should improve throttling rate
2. Timeout handling needs investigation
3. Validation errors are minimal (2%)
```

---

## Next Steps After Testing

1. **Analyze Results:**
   - Success rate improved with retries?
   - P95 latency improved?
   - Identify main failure category

2. **Adjust If Needed:**
   - Increase max_retries if throttling persists
   - Adjust concurrency if too many timeouts
   - Review Bedrock API quota usage

3. **Document Findings:**
   - Create final report with test data
   - Recommend production SLA
   - Plan Task 4.6 - Security Hardening

---

## Additional Resources

- **Optimization Plan:** `TASK_4_5_OPTIMIZATION_PLAN.md`
- **VP Response:** `VP_FEEDBACK_RESPONSE_2026-09-01.md`
- **Job Parser Code:** `bedrock_poc/parsing/job_parser.py`
- **API Endpoint:** `bedrock_poc/api/jobs.py`
- **Test Suite:** `run_optimized_performance_tests.py`

---

**Quick Start Guide v1.0**  
**For Task 4.5 Performance Optimization**  
**Created: 2026-09-01**
