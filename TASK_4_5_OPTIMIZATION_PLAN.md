# Task 4.5 - Performance Optimization & Implementation Plan

**Date:** September 1, 2026  
**Status:** 🚧 In Progress - Optimization Phase 1 Complete  
**Repository:** https://github.com/srikanthbhompally8/bedrock-poc  
**Branch:** phase-3/authentication

---

## Executive Summary

VP feedback indicated Task 4.5 performance testing needs significant optimization:
- **Current:** 20.34% success rate (36/177 requests), P95 latency: 44 seconds
- **Root Cause:** Lack of retry logic, no concurrency controls, insufficient error categorization
- **Solution:** Implement automatic retry with exponential backoff, error categorization, and concurrency limits

---

## Optimization Phase 1: Completed ✅

### 1. Enhanced Job Parser with Retry Logic

**File:** `bedrock_poc/parsing/job_parser.py`

**Changes:**
- Added `RetryConfig` class for configurable retry behavior
  - `max_retries`: 3 (default)
  - `initial_backoff_ms`: 100
  - `max_backoff_ms`: 5000
  - `backoff_multiplier`: 2.0 (exponential)
  
- Implemented automatic retry for transient errors:
  - Bedrock throttling (429 errors, "rate exceeded")
  - Request timeouts (504 errors, "timed out")
  
- Added `FailureCategory` enum to classify errors:
  - `THROTTLING`: Rate-limited by Bedrock
  - `TIMEOUT`: Request timed out
  - `VALIDATION`: Input validation error (non-retryable)
  - `CONNECTION`: Network/connection error
  - `MODEL_ERROR`: Model configuration issue
  - `SUCCESS`: Successful parse

**Code Flow:**
```python
for attempt in range(retry_config.max_retries + 1):
    try:
        response = converse(...)  # Call Bedrock
        # Parse and return
    except Exception as e:
        category = _categorize_error(e)
        if should_retry(category):
            backoff_ms = retry_config.get_backoff_ms(attempt)
            sleep(backoff_ms / 1000)
        else:
            raise  # Non-retryable error
```

**Impact:** Automatic handling of transient errors without client intervention.

---

### 2. Updated API Endpoint with Proper Error Handling

**File:** `bedrock_poc/api/jobs.py`

**HTTP Status Codes:**
| Status | Condition | Action |
|--------|-----------|--------|
| 200 | Success | Return parsed JobDescription |
| 400 | Validation Error | Client should NOT retry (bad input) |
| 429 | Throttling | Client should retry with backoff |
| 503 | Service Unavailable | Client should retry |
| 504 | Gateway Timeout | Client should retry |
| 500 | Server Error | Log for investigation |

**Benefits:**
- Clients can implement retry logic based on status codes
- Distinguishes between permanent (400, 500) and transient (429, 503, 504) failures
- Provides actionable error messages

---

### 3. Alternative Optimized Parser with Concurrency Control

**File:** `bedrock_poc/parsing/job_parser_optimized.py`

**Features:**
- `ConcurrencyControl` class using asyncio semaphore
  - Limits concurrent Bedrock calls (default: 5)
  - Prevents overwhelming the API
  
- `ParseMetrics` class for detailed tracking:
  - Success/failure counts by category
  - Latency tracking (min, max, avg)
  - Retry attempt counting
  
- Async support for high-concurrency scenarios

**Use Case:** When running load tests or processing multiple jobs concurrently.

---

### 4. Optimized Performance Test Suite

**File:** `run_optimized_performance_tests.py`

**Features:**
- Async load testing with concurrent users
- Detailed failure categorization
- Per-endpoint metrics
- JSON report generation with detailed request logs

**Failure Categories Tracked:**
- `validation_error`: Input validation failures (400)
- `throttling`: Rate limit errors (429)
- `gateway_timeout`: Timeout errors (502, 504)
- `service_unavailable`: Service down (503)
- `server_error`: Application errors (500)
- `auth_error`: Authentication failures (401, 403)
- `client_timeout`: Client-side timeout
- `success`: Successful requests (< 400)

**Test Configuration:**
- 100 concurrent users
- 60-second duration
- Staggered request startup to simulate realistic load
- Detailed latency percentiles (P50, P95, P99)
- Per-endpoint breakdown

---

## Optimization Phase 2: Planned 🔄

### Tasks to Complete

#### 2.1 Performance Baseline Re-test
- [ ] Start development server with optimizations
- [ ] Run `run_optimized_performance_tests.py`
- [ ] Collect metrics:
  - Success rate comparison (before/after)
  - Response time improvements
  - Failure category breakdown
  
**Expected Improvements:**
- Success rate: 20.34% → 60%+ (with automatic retries)
- P95 latency: 44s → 10-15s (timeout handling)
- Identified failure causes (throttling vs timeout vs validation)

#### 2.2 Client-Side Retry Implementation (Optional)
If load test results show persistent throttling:
- Implement exponential backoff in test client
- Add jitter to prevent thundering herd
- Track retry effectiveness

#### 2.3 Async Processing Evaluation
- Benchmark current synchronous parsing
- Implement async variant if needed
- Measure latency improvements

#### 2.4 Concurrency Control Tuning
Current setting: 5 concurrent Bedrock calls
- Monitor actual throttling rate
- Adjust if needed (reduce = lower throughput, increase = more throttling)

---

## Implementation Details

### Retry Logic Behavior

**Exponential Backoff Timeline:**
```
Attempt 1: Fails → Wait 100ms
Attempt 2: Fails → Wait 200ms
Attempt 3: Fails → Wait 400ms
Attempt 4: Fails → Return error (non-retryable or max retries exceeded)
```

### Error Categorization Logic

```python
def _categorize_error(error):
    if "throttling" in str(error) or "429" in str(error):
        return THROTTLING  # Retryable
    if "timeout" in str(error) or "504" in str(error):
        return TIMEOUT     # Retryable
    if "validation" in str(error) or "too short" in str(error):
        return VALIDATION  # NOT retryable
    if "connection" in str(error):
        return CONNECTION  # Retryable
    if "model" in str(error) or "enabled" in str(error):
        return MODEL_ERROR # NOT retryable
    return CONNECTION      # Default: assume network issue
```

### Concurrency Control

**Semaphore-based limiting:**
```python
semaphore = asyncio.Semaphore(5)  # Max 5 concurrent

async def execute():
    async with semaphore:
        return await bedrock_api.converse(...)
```

**Benefit:** Prevents overwhelming Bedrock with too many simultaneous requests.

---

## Testing Strategy

### Phase 2a: Baseline Comparison
Run both old and new performance tests:
```bash
# Old test (for reference)
python run_complete_performance_tests.py

# New optimized test
python run_optimized_performance_tests.py
```

### Phase 2b: Failure Analysis
Expected failure breakdown (without client retry):
- Validation errors: ~1-2% (bad job descriptions)
- Throttling: 5-10% (rate limiting)
- Timeouts: 10-20% (slow Bedrock responses)
- Connection errors: 1-5% (network issues)
- Successes: 60-80% (with automatic retries)

### Phase 2c: Load Testing Scenarios
1. **Baseline (10 users):** Measure success rate and latency
2. **Load (100 users):** Identify bottlenecks
3. **Stress (gradual increase):** Find breaking points

---

## Deployment Checklist

Before pushing to production:

- [ ] Run optimized performance tests
- [ ] Verify success rate > 80% (with auto-retries)
- [ ] Verify P95 latency < 15 seconds
- [ ] Test with actual job descriptions (not synthetic)
- [ ] Monitor Bedrock API quotas and costs
- [ ] Implement application-level metrics/logging
- [ ] Add monitoring alerts for high error rates
- [ ] Document retry behavior for API consumers
- [ ] Load test with production-like data volumes

---

## Configuration References

### Bedrock Client Config (bedrock_poc/client.py)
Already includes:
```python
boto_config = Config(
    retries={"max_attempts": 3, "mode": "standard"},
    read_timeout=60,
    connect_timeout=10,
)
```

### Job Parser Retry Config (bedrock_poc/parsing/job_parser.py)
Customizable:
```python
retry_config = RetryConfig(
    max_retries=3,
    initial_backoff_ms=100,
    max_backoff_ms=5000,
    backoff_multiplier=2.0
)
```

### API Concurrency Control (bedrock_poc/api/jobs.py)
Suggested limits (per instance):
- Development: 5 concurrent (current)
- Staging: 10 concurrent
- Production: 20 concurrent (depends on quota)

---

## Next Steps

1. **Today:** 
   - Start development server
   - Run optimized performance tests
   - Collect detailed metrics

2. **Tomorrow:**
   - Analyze results and compare with baseline
   - Adjust retry config if needed
   - Document findings in final report

3. **This Week:**
   - Finalize Task 4.5 performance report
   - Begin Task 4.6 - Security Hardening

---

## Files Modified/Created

### Modified:
- `bedrock_poc/parsing/job_parser.py` - Added retry logic
- `bedrock_poc/api/jobs.py` - Updated error handling

### Created:
- `bedrock_poc/parsing/job_parser_optimized.py` - Async variant with concurrency control
- `run_optimized_performance_tests.py` - New test suite with detailed metrics

### Git Commit:
```
9b4ec89 feat: Implement Task 4.5 performance optimizations with retry logic and error categorization
```

---

## Conclusion

Phase 1 of Task 4.5 optimization is complete. The job parser now includes:
- ✅ Automatic retry logic for transient failures
- ✅ Error categorization (6 categories)
- ✅ Proper HTTP status codes for different error types
- ✅ Configurable retry behavior with exponential backoff
- ✅ Optional async/concurrent processing path

**Expected Outcome:** Success rate improvement from 20.34% to 60%+ with automatic retries.

**Next Phase:** Run performance tests to validate improvements and establish new baseline metrics.

---

**Document Version:** 1.0  
**Last Updated:** 2026-09-01  
**Status:** Ready for Phase 2 Testing
