# AWS Bedrock Setup & Configuration Guide

## Overview

This guide covers the AWS Bedrock configuration required to run the POC application.
No additional AWS services are required beyond Bedrock itself.

## AWS Bedrock Models

### Primary Model: Claude 3.5 Sonnet

**Model ID:** `us.anthropic.claude-3-5-sonnet-20241022-v2:0`

**Used for:**
- Chat conversations
- Document summarization
- Q&A (grounded and RAG-enhanced)
- Resume parsing with structured output

**Pricing:**
- Input: $0.003 per 1K tokens
- Output: $0.015 per 1K tokens
- Estimated cost per call: $0.01-0.05

**Reasoning:**
- Claude 3.5 Sonnet offers the best balance of cost and capability
- Supports structured output (important for resume parsing)
- Available in us-east-1 (free tier available)

### Embeddings Model: Titan Text Embeddings v2

**Model ID:** `amazon.titan-embed-text-v2:0`

**Used for:**
- RAG semantic search (chunking + retrieval)
- Converts text to vector embeddings
- Used internally, not exposed to users

**Pricing:**
- $0.02 per 1M tokens
- Very affordable for embedding operations

**Reasoning:**
- Native AWS service, no external API dependency
- Dimensions: 1024 (good balance of quality and performance)
- Optimized for semantic search

## IAM Permissions

### Minimum Policy for POC

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }
  ]
}
```

### For EC2 Deployment

Attach the above policy to the EC2 instance's IAM role:

```bash
# Create role
aws iam create-role \
  --role-name bedrock-poc-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach policy
aws iam put-role-policy \
  --role-name bedrock-poc-role \
  --policy-name bedrock-access \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }]
  }'

# Create instance profile and attach
aws iam create-instance-profile --instance-profile-name bedrock-poc-profile
aws iam add-role-to-instance-profile \
  --instance-profile-name bedrock-poc-profile \
  --role-name bedrock-poc-role
```

## Model Access in Bedrock Console

Before running the application, you must enable model access in the AWS Bedrock console.

**Steps:**

1. Log into AWS Console
2. Navigate to **Amazon Bedrock**
3. In the left sidebar, click **Model access**
4. Click **Modify model access** (top right)
5. Search for and enable:
   - ✅ **Claude 3.5 Sonnet** (us.anthropic.claude-3-5-sonnet-20241022-v2:0)
   - ✅ **Titan Text Embeddings v2** (amazon.titan-embed-text-v2:0)
6. Click **Save changes**
7. Wait 1-2 minutes for access to be provisioned

**Note:** Model access is account-specific. Each AWS account must enable models.

## Environment Configuration

### Development Setup

Create a `.env` file in the project root:

```bash
# .env
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0

# Optional: AWS credentials (if not using default chain)
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
```

Or set environment variables directly:

```bash
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
```

### AWS Credentials Resolution

The application uses boto3's default credential chain:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. AWS credentials file (`~/.aws/credentials`)
3. AWS config file (`~/.aws/config`)
4. IAM role (when running on EC2, ECS, Lambda)

**Recommended for EC2:**
- Use EC2 instance IAM role (no credentials in config files)
- Never store access keys in environment variables on shared systems

## Regional Availability

Claude 3.5 Sonnet and Titan Embeddings are available in:
- ✅ **us-east-1** (N. Virginia) — **Recommended for this POC**
- ✅ **us-west-2** (N. California)
- ✅ **eu-central-1** (Frankfurt)
- ✅ **ap-southeast-1** (Singapore)

**Note:** Model IDs may vary by region. If you get an "invalid model ID" error, 
check the exact model ID in the Bedrock console for your region.

## Pricing & Cost Estimates

### Per-Feature Costs (Approximate)

| Feature | Call Type | Est. Tokens | Est. Cost |
|---------|-----------|------------|-----------|
| Chat Turn | 1 message + context | 500 in / 200 out | $0.002 |
| Summarize | 1 page doc | 2000 in / 300 out | $0.008 |
| Q&A | 5K doc + question | 5500 in / 200 out | $0.018 |
| RAG Q&A | Embeddings + search | 500 in / 200 out | $0.003 (+ embed cost) |
| Resume Parse | 1 page resume | 1000 in / 300 out | $0.004 |
| Embed Text | 1000 chars | 300 tokens | $0.000006 |

### Monthly Estimates

**Light Usage (100 API calls/month)**
```
Chat: 100 calls × $0.002 = $0.20
Summarize: 20 calls × $0.008 = $0.16
Q&A: 30 calls × $0.018 = $0.54
RAG: 20 calls × $0.003 = $0.06
Resume: 10 calls × $0.004 = $0.04
Embeddings: 1000 calls × $0.000006 = $0.006
─────────────────────────────────
Total: ~$1.00/month
```

**Heavy Usage (10K API calls/month)**
```
Chat: 3000 calls × $0.002 = $6.00
Summarize: 1000 calls × $0.008 = $8.00
Q&A: 3000 calls × $0.018 = $54.00
RAG: 2000 calls × $0.003 = $6.00
Resume: 500 calls × $0.004 = $2.00
Embeddings: 50000 calls × $0.000006 = $0.30
─────────────────────────────────
Total: ~$76.30/month
```

**Plus EC2 infrastructure:**
- t3.micro on-demand: ~$10/month
- Data transfer: ~$1/month

## Testing AWS Setup

Before running the full application, verify your Bedrock setup:

```bash
# Install boto3
pip install boto3

# Test connection (Python script)
python -c "
import boto3
client = boto3.client('bedrock-runtime', region_name='us-east-1')
print('✓ Connected to Bedrock')
"

# List available models
aws bedrock list-foundation-models --region us-east-1

# Test Claude API call
python -c "
import boto3
client = boto3.client('bedrock-runtime', region_name='us-east-1')
response = client.converse(
    modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
    messages=[{'role': 'user', 'content': [{'text': 'Hello'}]}],
    system=[{'text': 'You are helpful.'}]
)
print('✓ Claude API working')
print(response['output']['message']['content'][0]['text'])
"

# Test Titan Embeddings
python -c "
import boto3
import json
client = boto3.client('bedrock-runtime', region_name='us-east-1')
response = client.invoke_model(
    modelId='amazon.titan-embed-text-v2:0',
    body=json.dumps({'inputText': 'Hello world'})
)
print('✓ Titan Embeddings working')
"
```

## Troubleshooting

### "Invalid model ID" Error
- **Cause:** Model not enabled or incorrect ID for your region
- **Fix:** Go to Bedrock console → Model access → Copy exact model ID

### "Access Denied" / 403 Error
- **Cause:** IAM policy missing or credentials invalid
- **Fix:** Verify IAM policy has `bedrock:InvokeModel` permission

### "ValidationException" Error
- **Cause:** Invalid parameter (e.g., wrong region, wrong model)
- **Fix:** Ensure `AWS_REGION` and `BEDROCK_MODEL_ID` match console values

### "ThrottlingException" Error
- **Cause:** Rate limit exceeded (Bedrock has per-account limits)
- **Fix:** Implement exponential backoff (boto3 retries automatically)

### "Unknown service" Error
- **Cause:** boto3 version too old
- **Fix:** Update: `pip install --upgrade boto3`

## API Limits

### Bedrock Rate Limits

| Limit | Value | Note |
|-------|-------|------|
| **Input tokens per request** | 200k | Claude can handle large documents |
| **Output tokens per request** | 2k-4k | Varies by model |
| **Requests per second** | 100 | Per account, shared across models |
| **Concurrent connections** | Unlimited | Throttled by RPS limit |

### POC Application Limits

These are self-imposed for safety:
- Max document size (non-RAG): 40k chars (prevents truncation warnings)
- Max document size (RAG): Unlimited (chunked and searched)
- Max resume size: 100k chars (PDF extraction)
- Max concurrent sessions: 1 (Streamlit limitation)

## Security Best Practices

1. **Never commit credentials**
   ```bash
   # Good: Use .env (gitignored)
   export $(cat .env | xargs)
   
   # Bad: Hardcode in code
   # AWS_ACCESS_KEY_ID = "AKIA..."
   ```

2. **Use IAM roles on EC2**
   - Attach role instead of storing keys
   - Credentials rotate automatically
   - No .env file needed on EC2

3. **Limit Bedrock permissions**
   - Only grant `bedrock:InvokeModel` for runtime
   - Separate "deploy" role for CI/CD if needed

4. **Monitor costs**
   - Set CloudWatch alarms for budget
   - Review Bedrock pricing dashboard monthly
   - Log all API calls to CloudTrail

5. **Rate limit in production**
   - Add API Gateway or Lambda authorizer
   - Implement per-user quotas
   - Prevent DoS via excessive API calls

## Model Migration

To switch models (e.g., from Sonnet to Opus), only change one environment variable:

```bash
# Before
export BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0

# After (no code changes!)
export BEDROCK_MODEL_ID=us.anthropic.claude-3-opus-4-1-20250514:0
```

Verify new model is enabled in Bedrock console first.

## Bedrock Knowledge Base (Future)

For production RAG, consider using Bedrock Knowledge Base instead of the
in-memory vector store:

- Persistent vector storage (managed by AWS)
- No need to embed documents on every request
- Automatic chunking and indexing
- Built-in retrieval APIs

This POC uses in-memory embeddings for simplicity and cost.

## Support & Resources

- **AWS Bedrock Console:** https://console.aws.amazon.com/bedrock
- **Bedrock Pricing:** https://aws.amazon.com/bedrock/pricing/
- **Claude Documentation:** https://docs.anthropic.com/
- **boto3 Bedrock Docs:** https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock.html
- **Bedrock Runtime API:** https://docs.aws.amazon.com/bedrock/latest/APIReference/

## Verification Checklist

- [ ] AWS account created and Bedrock enabled
- [ ] Claude 3.5 Sonnet model access granted (Bedrock console)
- [ ] Titan Text Embeddings v2 model access granted (Bedrock console)
- [ ] IAM policy with `bedrock:InvokeModel` created
- [ ] AWS credentials configured (env vars or ~/.aws/credentials)
- [ ] `AWS_REGION` and `BEDROCK_MODEL_ID` environment variables set
- [ ] Test script runs successfully (see "Testing AWS Setup" section)
- [ ] EC2 instance has appropriate IAM role (for deployment)
- [ ] Cost alerts configured in AWS Billing console

Once all items are checked, run: `python -m pytest tests/` to verify everything.
