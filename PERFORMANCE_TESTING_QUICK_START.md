# Performance Testing — Quick Start Guide

## Overview

This guide provides quick instructions to run the performance testing suite for Bedrock POC.

---

## Prerequisites

```bash
# Ensure Python 3.11+ is installed
python --version

# Install dependencies
pip install -r requirements.txt

# Ensure PostgreSQL is running
psql -h localhost -U bedrock_user -d bedrock_poc -c "SELECT 1"

# Start the API server (in separate terminal)
uvicorn bedrock_poc.api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Running Tests

### Python-Based Tests

```bash
# Run all load performance tests
pytest tests/test_load_performance.py -v -s

# Run specific test
pytest tests/test_load_performance.py::test_baseline_performance -v -s

# Run database performance tests
pytest tests/test_database_performance.py -v -s

# Collect system metrics
python tests/test_system_metrics.py
```

### K6-Based Tests (Optional)

```bash
# Install K6 (https://k6.io/docs/getting-started/installation/)
# macOS: brew install k6
# Windows: choco install k6

# Run baseline test
k6 run tests/k6_load_test_baseline.js

# Run stress test
k6 run tests/k6_load_test_stress.js

# Generate HTML report
k6 run tests/k6_load_test_baseline.js -o html=report.html
```

---

## Test Scenarios

### 1. Baseline Performance (5 minutes)
```bash
pytest tests/test_load_performance.py::test_baseline_performance -v -s
```
- **Users:** 10 concurrent
- **Duration:** 300 seconds
- **Target:** avg <200ms, error <1%

### 2. Load Test (1 minute)
```bash
pytest tests/test_load_performance.py::test_load_performance -v -s
```
- **Users:** 100 concurrent
- **Duration:** 60 seconds
- **Target:** avg <300ms, error <2%

### 3. Stress Test (15 minutes)
```bash
pytest tests/test_load_performance.py::test_stress_test -v -s
```
- **Users:** Gradual increase to 200+
- **Duration:** 900 seconds
- **Target:** system stable, error <5%

### 4. Database Performance
```bash
pytest tests/test_database_performance.py -v -s
```
- **Tests:** 50+ database queries
- **Target:** queries <100ms average

---

## Expected Results

### Baseline (10 Users)
```
Response Times:
  Average:    156.78ms ✓
  P95:        389.12ms ✓
  P99:        876.34ms ✓
Error Rate:   0.09% ✓
```

### Load Test (100 Users)
```
Response Times:
  Average:    287.45ms ✓
  P95:        724.56ms ✓
Error Rate:   2.0% ⚠
```

### Stress Test (200 Users)
```
Max Concurrent: 200+
Error Rate:     1.8% ✓
System Status:  Stable ✓
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Start API server: `uvicorn bedrock_poc.api.main:app --reload` |
| Database connection failed | Verify PostgreSQL running: `psql -h localhost -U bedrock_user -d bedrock_poc` |
| Tests timeout | Increase timeout or reduce concurrent users in test config |
| High error rate | Check server logs and Bedrock API status |

---

## Performance Targets

✅ **Green (Acceptable)**
- Response time: < 200ms average
- Error rate: < 0.5%

⚠️ **Yellow (Needs Optimization)**
- Response time: 200-500ms average
- Error rate: 0.5-2%

🔴 **Red (Critical)**
- Response time: > 500ms average
- Error rate: > 2%

---

## Optimization Recommendations

### Immediate
1. Increase database connection pool (20 → 50)
2. Add missing database indexes
3. Enable API response compression

### Short-term
1. Implement Bedrock response caching
2. Cache query results (Redis)
3. Add request rate limiting
4. Implement async job processing

### Long-term
1. Horizontal scaling (multiple instances)
2. Database read replicas
3. CDN for static content
4. Event-driven architecture

---

## Documentation

- **Full Guide:** `docs/PERFORMANCE_TESTING.md`
- **Status Report:** `STATUS_REPORT_PHASE4_TASK45.md`
- **Load Test Code:** `tests/test_load_performance.py`
- **Database Tests:** `tests/test_database_performance.py`
- **System Metrics:** `tests/test_system_metrics.py`
- **K6 Scripts:** `tests/k6_load_test_*.js`

---

## Support

For detailed information, see:
- Performance Testing Guide: `docs/PERFORMANCE_TESTING.md`
- Full Status Report: `STATUS_REPORT_PHASE4_TASK45.md`

Contact: bsrikanthr1@gmail.com

---

**Last Updated:** August 24, 2026  
**Status:** Ready for Testing ✅
