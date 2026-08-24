# Running Performance Tests on Windows PowerShell

## Step 1: Navigate to Project Directory

```powershell
cd C:\Users\bhomp\Downloads\bedrock-poc\bedrock-poc
```

Verify you're in the correct directory:
```powershell
ls bedrock_poc  # Should show folders like api, auth, config, logging, monitoring, etc.
```

---

## Step 2: Ensure Python Virtual Environment is Activated

```powershell
# Check if virtual environment is activated (should show (.venv) in prompt)
# If not, activate it:
.\.venv\Scripts\Activate.ps1

# Verify Python and pip work
python --version
pip list | Select-String pytest
```

---

## Step 3: Start the API Server (in a NEW PowerShell window)

```powershell
# In a separate PowerShell window, navigate to project and run:
cd C:\Users\bhomp\Downloads\bedrock-poc\bedrock-poc
.\.venv\Scripts\Activate.ps1
uvicorn bedrock_poc.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

---

## Step 4: Run Performance Tests

### Run All Tests in test_load_performance.py

```powershell
pytest tests/test_load_performance.py -v -s
```

**Expected output:**
```
test_api_health PASSED
test_baseline_performance PASSED
test_load_performance PASSED
test_stress_test PASSED
```

### Run Specific Test

```powershell
# Baseline performance test only (shortest - ~5 min)
pytest tests/test_load_performance.py::test_baseline_performance -v -s

# Load test only (~1 min)
pytest tests/test_load_performance.py::test_load_performance -v -s

# Stress test only (~15 min)
pytest tests/test_load_performance.py::test_stress_test -v -s
```

### Run Database Performance Tests

```powershell
pytest tests/test_database_performance.py -v -s
```

**Note:** Database must be running. If tests fail, ensure PostgreSQL is running:
```powershell
# Check if PostgreSQL is running
Get-Service postgres* | Select Name, Status

# If not running, start it:
Start-Service postgres*
```

### Run System Metrics Collection

```powershell
python tests/test_system_metrics.py
```

---

## Step 5: View Results

After each test, you'll see output like:

```
SCENARIO: Baseline Performance (10 Users)
Concurrent Users:        10
Duration:                300s
Total Requests:          3,250
Successful Requests:     3,247
Failed Requests:         3
Error Rate:              0.09%
Throughput:              10.83 req/sec

Response Times (ms):
  Min:                   45.23ms
  Max:                   1,243.56ms
  Average:               156.78ms ✓
  P50 (Median):          142.45ms
  P95:                   389.12ms ✓
  P99:                   876.34ms ✓
```

---

## Quick Test Sequence (Start Small)

For your first run, test in this order:

```powershell
# 1. Health check (takes <5 seconds)
pytest tests/test_load_performance.py::test_api_health -v -s

# 2. Baseline performance (takes ~5 minutes)
pytest tests/test_load_performance.py::test_baseline_performance -v -s

# 3. Load test (takes ~1 minute)
pytest tests/test_load_performance.py::test_load_performance -v -s

# 4. Stress test (takes ~15 minutes)
pytest tests/test_load_performance.py::test_stress_test -v -s

# 5. Database tests (takes ~2 minutes)
pytest tests/test_database_performance.py -v -s
```

**Total time: ~25 minutes**

---

## Troubleshooting

### Error: "file or directory not found"

**Cause:** You're in the wrong directory

**Solution:**
```powershell
cd C:\Users\bhomp\Downloads\bedrock-poc\bedrock-poc
```

### Error: "Connection refused" or "Cannot connect to localhost:8000"

**Cause:** API server is not running

**Solution:** Start the API server in a separate PowerShell window (see Step 3)

### Error: "Database connection failed"

**Cause:** PostgreSQL is not running

**Solution:**
```powershell
# Start PostgreSQL
Start-Service postgres*

# Verify it's running
Get-Service postgres* | Select Name, Status
```

### Error: "asyncio" or "httpx" not found

**Cause:** Dependencies not installed

**Solution:**
```powershell
pip install -r requirements.txt
```

### Tests timeout

**Cause:** API server is slow or not responding

**Action:** 
1. Check API server logs
2. Verify database connectivity
3. Reduce concurrent users in test config
4. Increase timeout in LoadTestConfig.TIMEOUT

---

## Performance Success Criteria

✅ **PASS** if you see:
- Baseline: avg <200ms, error <1%
- Load test: avg <300ms, error <2%
- Stress test: system stable, error <5%
- Database: queries <100ms avg

❌ **FAIL** if you see:
- High error rates (>5%)
- Response times >500ms avg
- Timeouts or connection errors
- Database connection exhaustion

---

## Next Steps After Testing

1. **Review Results**
   - Compare against expected benchmarks
   - Check for any concerning metrics

2. **Check Documentation**
   - Full guide: `docs/PERFORMANCE_TESTING.md`
   - Optimization recommendations: `STATUS_REPORT_PHASE4_TASK45.md`

3. **Analyze Bottlenecks**
   - Identify slow endpoints
   - Check system resource usage
   - Review database query performance

4. **Implement Optimizations**
   - See recommendations in status report
   - Prioritize connection pool expansion
   - Add database indexes
   - Implement caching

---

## For Detailed Information

See these files for complete documentation:
- `PERFORMANCE_TESTING_QUICK_START.md` — Quick reference
- `docs/PERFORMANCE_TESTING.md` — Complete guide
- `STATUS_REPORT_PHASE4_TASK45.md` — Detailed analysis
- `tests/test_load_performance.py` — Source code

---

## K6 Alternative (Optional)

If you want to use K6 for load testing:

```powershell
# Install K6 (requires Chocolatey or manual download)
choco install k6

# Run baseline test
k6 run tests/k6_load_test_baseline.js

# Run stress test
k6 run tests/k6_load_test_stress.js

# Generate HTML report
k6 run tests/k6_load_test_baseline.js -o html=report.html
```

---

**Last Updated:** August 24, 2026  
**Status:** Ready for Testing ✅
