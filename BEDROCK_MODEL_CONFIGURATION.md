# Bedrock Model Configuration & Troubleshooting

**Date:** 2026-08-25  
**Issue:** Task 4.5 Performance Testing - Bedrock Model Configuration

## Problem Summary

The job parsing endpoint was returning 500 errors due to incorrect or unavailable Bedrock model configuration. Root cause analysis identified two issues:

1. **Deprecated Model ID Format**: Initial configuration used regional prefix format `us.anthropic.claude-3-5-sonnet-20241022-v2:0` which has reached end-of-life
2. **Settings Caching**: Python's `@lru_cache()` decorator on `get_settings()` prevented configuration updates from being loaded

## Resolution Steps

### 1. Verify Available Models in AWS Bedrock Console

**Action Required:**
- Navigate to AWS Console → Amazon Bedrock → Model access
- Review available Claude models in your region (us-east-1)
- Check which models have "Available" status
- Note the exact model ID format shown in the console

**Current Status:** Diagnostic testing shows NO available Claude models:
- Claude 3.x, 3.5 Sonnet: End-of-life (ResourceNotFoundException)
- Claude 4.x, Haiku 4.5: Invalid identifiers (ValidationException)
- Claude 3 Haiku: Legacy access denied

### 2. Configuration Methods

The application supports configurable Bedrock model IDs through two mechanisms:

**Method A: Environment Variable (Recommended)**
```bash
export BEDROCK_MODEL_ID="anthropic.claude-xxx-yyyyyyy"
uvicorn bedrock_poc.api.main:app --host 0.0.0.0 --port 8000
```

**Method B: Configuration File**
Edit `bedrock_poc/config/settings.py` line 85:
```python
model_id: str = Field(
    default="anthropic.claude-xxx-yyyyyyy",  # Update this
    description="Bedrock model ID",
)
```

### 3. Settings Caching Issue

**Problem:** The `get_settings()` function in `bedrock_poc/config/settings.py` uses `@lru_cache()` which caches the settings object. Configuration changes don't take effect without full Python process restart.

**Solution:** Always restart the API server process when changing model IDs:
1. Stop the server: `Ctrl+C`
2. Wait 2 seconds
3. Set environment variable and restart:
   ```bash
   export BEDROCK_MODEL_ID="model-id-here"
   uvicorn bedrock_poc.api.main:app --host 0.0.0.0 --port 8000
   ```

### 4. Model ID Format Variations

Different Bedrock regions may require different model ID formats:

| Format | Example | Notes |
|--------|---------|-------|
| Non-regional | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Standard format |
| Regional prefix | `us.anthropic.claude-3-5-sonnet-20241022-v2:0` | Some accounts/regions |
| Without suffix | `anthropic.claude-3-5-sonnet-20241022-v2` | Alternative format |

**Check AWS Bedrock console for correct format in your account.**

### 5. Validation Process

**Before running performance tests:**

1. **Direct API Test:**
   ```bash
   python test_bedrock_models.py
   ```
   This will validate which models are available in your Bedrock account.

2. **Manual Endpoint Test:**
   ```powershell
   # Login and get token
   $loginBody = @{
       email = "testuser@example.com"
       password = "TestPassword123!"
   } | ConvertTo-Json

   $loginResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/login" `
       -Method POST -Body $loginBody -ContentType "application/json" -UseBasicParsing

   $token = ($loginResponse.Content | ConvertFrom-Json).access_token

   # Test job parsing
   $parseBody = @{
       job_description = "Senior Python Developer - 5 years required"
   } | ConvertTo-Json

   $headers = @{
       "Authorization" = "Bearer $token"
       "Content-Type" = "application/json"
   }

   Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/parse" -Method POST `
       -Body $parseBody -Headers $headers -UseBasicParsing -ErrorAction Stop
   ```

## Next Steps

1. **Enable a Claude Model in AWS Bedrock Console**
   - Log into AWS Console
   - Go to Amazon Bedrock → Model access
   - Find an available Claude model
   - Enable it if needed
   - Copy the exact model ID

2. **Set Environment Variable**
   ```bash
   export BEDROCK_MODEL_ID="<model-id-from-console>"
   ```

3. **Restart API Server**
   ```bash
   uvicorn bedrock_poc.api.main:app --host 0.0.0.0 --port 8000
   ```

4. **Validate with Direct Test**
   ```bash
   python test_bedrock_models.py
   ```

5. **Run Performance Tests**
   ```bash
   python run_performance_tests_fixed.py
   ```

## Technical Details

### Configuration Loading Chain

1. `bedrock_poc/client.py:get_model_id()` → Reads `BEDROCK_MODEL_ID` env var
2. Falls back to `DEFAULT_MODEL_ID` if env var not set
3. Passed to `bedrock_poc/config/settings.py` BedrockSettings class
4. Used in `bedrock_poc/parsing/job_parser.py` when calling Bedrock API

### Error Messages Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `ResourceNotFoundException: This model version has reached the end of its life` | Model is deprecated | Use newer model ID |
| `ValidationException: The provided model identifier is invalid` | Wrong format or model not enabled | Check AWS console for correct format |
| `Access denied. Model is marked as Legacy` | Model not actively used in 30 days | Enable newer model or request access |
| `Failed to parse job description: Bedrock request failed` | API server misconfigured | Restart server with correct env var |

## Files Modified

- `bedrock_poc/config/settings.py` - Line 85: Model ID configuration
- `bedrock_poc/client.py` - Line 31: Default model and env var reading logic
- `run_performance_tests_fixed.py` - Wrapper script with env var setup

## Prevention for Future Deployments

1. **Document available models in each region** before deployment
2. **Test model availability** with `test_bedrock_models.py` before running load tests
3. **Never hardcode model IDs** - always use environment configuration
4. **Add validation step** to CI/CD pipeline to confirm model availability
5. **Monitor for model deprecation** notices from AWS

---

**Status:** Awaiting model enablement in AWS Bedrock Console  
**Action Required:** User must enable Claude model in AWS Console and update `BEDROCK_MODEL_ID` environment variable
