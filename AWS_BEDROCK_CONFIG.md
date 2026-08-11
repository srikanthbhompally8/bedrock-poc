# AWS Bedrock Configuration Details

**Last Updated:** July 24, 2026  
**Status:** ✅ Production Ready

---

## **QUICK REFERENCE**

| Configuration | Value |
|---|---|
| **Service** | Amazon Bedrock |
| **Region** | us-east-1 |
| **Primary Model** | Claude 3.5 Sonnet |
| **Embedding Model** | Titan Text Embeddings v2 |
| **API Type** | Converse API |
| **Pricing Model** | Pay-per-token |

---

## **MODELS CONFIGURED**

### **1. Claude 3.5 Sonnet (Text Generation)**

**Model ID:** `us.anthropic.claude-3-5-sonnet-20241022-v2:0`

**Used For:**
- Chat conversations (multi-turn)
- Document summarization
- Question answering
- Resume parsing
- All text generation tasks

**Capabilities:**
- Context window: 200,000 tokens
- Max output: 4,096 tokens
- Streaming: ✅ Yes
- Temperature range: 0.0 - 1.0
- Instruction following: Excellent

**Pricing:**
- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens
- Example: 1,000 input + 500 output tokens = ~$0.0045

**Why This Model?**
- Best-in-class performance
- Excellent reasoning and coding abilities
- Great for structured output
- Reliable for production use

---

### **2. Titan Text Embeddings v2 (Vector Embeddings)**

**Model ID:** `amazon.titan-embed-text-v2:0`

**Used For:**
- Converting text to vector embeddings (RAG feature)
- Semantic similarity search
- Document chunk retrieval

**Capabilities:**
- Output dimension: 1,536
- Max input tokens: 8,192
- Batch processing: ✅ Yes
- Streaming: ❌ No

**Pricing:**
- $0.02 per 1M input tokens
- Example: 10,000 tokens = ~$0.0002

**Why This Model?**
- Optimized for semantic search
- Low latency
- Cost-effective
- Native AWS integration
- Excellent for RAG workflows

---

## **API CONFIGURATION**

### **Converse API** (Main Interface)

Used for all text generation tasks:

```python
client.converse(
    modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    messages=[...],
    system="...",
    inferenceConfig={
        "maxTokens": 1024,
        "temperature": 0.5
    }
)
```

**Advantages:**
- Unified API for all models
- System prompt support
- Streaming capability
- Multi-turn conversation history
- No model-specific JSON formatting

### **Invoke Model API** (Embeddings)

Used for generating embeddings:

```python
client.invoke_model(
    modelId="amazon.titan-embed-text-v2:0",
    body=json.dumps({"inputText": "text to embed"}),
    contentType="application/json"
)
```

---

## **REGION CONFIGURATION**

**Selected Region:** `us-east-1` (N. Virginia, USA)

**Why this region?**
- ✅ All Bedrock models available
- ✅ Lowest latency for most users
- ✅ Best cost (pricing differences are minimal)
- ✅ EC2 instance located in same region

**Alternative Regions (if needed):**
- us-west-2 (Oregon) - Good for West Coast
- eu-west-1 (Ireland) - For European users
- ap-southeast-1 (Singapore) - For Asia-Pacific

**Note:** Model availability varies by region. Claude 3.5 Sonnet is available in:
- us-east-1 ✅
- us-west-2 ✅
- eu-west-1 ✅
- ap-southeast-1 ✅

---

## **IAM PERMISSIONS REQUIRED**

### **Minimum Permissions**

Create IAM policy with these permissions:

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

### **Recommended Permissions** (With monitoring)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:GetFoundationModelAvailability",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```

### **How to Apply**

1. Go to AWS IAM Console
2. Create new policy → Paste JSON above
3. Attach to your IAM user/role
4. Test with: `aws bedrock list-foundation-models --region us-east-1`

---

## **MODEL ACCESS SETUP**

### **Enable Models in Bedrock Console**

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Click **"Model access"** (left sidebar)
3. Click **"Manage model access"**
4. Enable:
   - ✅ Claude 3.5 Sonnet
   - ✅ Titan Text Embeddings v2
5. Click **"Save changes"**
6. Wait 5-10 minutes for activation

### **Verify Access**

```bash
# List available models
aws bedrock list-foundation-models --region us-east-1 --by-provider anthropic
```

Should return Claude 3.5 Sonnet in the list.

---

## **TEMPERATURE & INFERENCE SETTINGS**

### **Temperature Explained**

Temperature controls randomness/creativity:
- **0.0** = Deterministic (same response every time)
- **0.5** = Balanced (some variation)
- **1.0** = Creative (very random)

### **Settings by Use Case**

| Use Case | Temperature | Reason |
|---|---|---|
| Chat | 0.5 | Some variety but still coherent |
| Summarization | 0.2 | Consistent, faithful summaries |
| Q&A | 0.1 | Precise, grounded answers |
| Resume Parsing | 0.1 | Consistent structure extraction |
| RAG | 0.1 | Reliable retrieval-based answers |

### **Max Tokens by Use Case**

| Use Case | Max Tokens | Reason |
|---|---|---|
| Chat | 1024 | Conversational responses |
| Summarization | 512 | Concise summaries |
| Q&A | 512 | Short, focused answers |
| Resume Parsing | 2000 | Complex JSON structure |

---

## **COST ESTIMATION**

### **Monthly Usage Projection**

Based on POC traffic (10 requests/day):

```
Daily Usage:
- Chat: 5 requests × (500 input + 300 output) = 4,000 tokens
- Q&A: 3 requests × (1000 input + 200 output) = 3,600 tokens
- Parse Resume: 1 request × (500 input + 1000 output) = 1,500 tokens
- Embeddings (RAG): 1 request × 5000 tokens = 5,000 tokens

Daily Total: ~14,100 tokens
Monthly Total: ~423,000 tokens
```

**Monthly Cost Breakdown:**

| Component | Tokens | Cost |
|---|---|---|
| Claude Input (423K tokens) | @ $3/1M | $1.27 |
| Claude Output (100K tokens) | @ $15/1M | $1.50 |
| Embeddings (50K tokens) | @ $0.02/1M | $0.00 |
| **Total/Month** | | **~$2.77** |

**Yearly: ~$33**

### **Scaling Scenarios**

| Scenario | Daily Requests | Monthly Cost |
|---|---|---|
| Current (POC) | 10 | $2-3 |
| Small Production | 100 | $25-30 |
| Medium Production | 1,000 | $250-300 |
| Large Production | 10,000 | $2,500-3,000 |

---

## **ENVIRONMENT VARIABLES**

### **Required in `.env` or System**

```bash
# Bedrock configuration
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
AWS_REGION=us-east-1

# AWS credentials (from aws configure or env vars)
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
```

### **Optional Configuration**

```bash
# Customize model behavior
BEDROCK_TEMPERATURE=0.5
BEDROCK_MAX_TOKENS=1024

# Logging
LOG_LEVEL=INFO
```

---

## **API RATE LIMITS**

### **Default Limits (per account)** 

| Metric | Limit | Applies To |
|---|---|---|
| Requests per second | 100 | All models |
| Concurrent requests | 100 | All models |
| Input tokens/minute | Varies | See model docs |
| Output tokens/minute | Varies | See model docs |

**Note:** These are typical limits. Check AWS console for your account limits.

### **How to Request Higher Limits**

1. Go to [Service Quotas Console](https://console.aws.amazon.com/servicequotas/)
2. Find "Bedrock"
3. Select the limit to increase
4. Click "Request quota increase"
5. Enter desired value
6. Submit (usually approved within hours)

---

## **MONITORING & LOGGING**

### **CloudWatch Metrics**

Bedrock automatically sends metrics to CloudWatch:

```bash
# View metrics
aws cloudwatch list-metrics --namespace "AWS/Bedrock" --region us-east-1
```

**Key Metrics:**
- InputTokens
- OutputTokens
- Invocations
- ThrottledRequests
- Latency

### **Enable Detailed Monitoring**

Add to code (if using CloudWatch):

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='BedrockPOC',
    MetricData=[
        {
            'MetricName': 'APIRequests',
            'Value': 1,
            'Unit': 'Count'
        }
    ]
)
```

### **CloudWatch Dashboard** (Optional)

Create dashboard to monitor:
- API request count
- Tokens used (input/output)
- Latency
- Error rate
- Cost

---

## **SECURITY BEST PRACTICES**

### **1. Credential Management**

✅ **DO:**
- Use IAM roles (not access keys when possible)
- Store credentials in AWS Secrets Manager
- Use temporary credentials (STS)
- Rotate keys regularly

❌ **DON'T:**
- Hardcode credentials in code
- Commit `.env` file to Git
- Share credentials in emails
- Use root account credentials

### **2. API Calls**

✅ **DO:**
- Use HTTPS (all Bedrock calls are encrypted)
- Validate input data
- Implement rate limiting
- Log all requests

❌ **DON'T:**
- Send sensitive data in plain text
- Disable SSL verification
- Use deprecated API versions

### **3. Cost Control**

✅ **DO:**
- Set token limits per request
- Monitor CloudWatch metrics
- Set up billing alerts
- Review usage regularly

❌ **DON'T:**
- Use unlimited tokens
- Allow unbounded loops
- Accept user-generated max_tokens without validation

### **4. Data Privacy**

✅ **DO:**
- Classify data sensitivity
- Encrypt at rest if storing
- Follow company data policies
- Get approval for data usage

❌ **DON'T:**
- Send PII to Bedrock without consent
- Store sensitive outputs permanently
- Share request/response logs externally

---

## **TROUBLESHOOTING**

### **Error: AccessDeniedException**

```
User is not authorized to perform: bedrock:InvokeModel
```

**Solution:**
1. Check IAM permissions (see above)
2. Verify model access enabled in Bedrock console
3. Ensure region is correct (us-east-1)
4. Wait 10 minutes after enabling model access

### **Error: ModelNotFoundException**

```
Could not find model: us.anthropic.claude-3-5-sonnet-20241022-v2:0
```

**Solution:**
1. Verify model is enabled in Bedrock console
2. Check region (not all models available in all regions)
3. Try listing models: `aws bedrock list-foundation-models`

### **Error: ThrottlingException**

```
Rate exceeded. Please retry after some time.
```

**Solution:**
1. Implement exponential backoff retry logic
2. Reduce concurrent requests
3. Request rate limit increase via Service Quotas

### **Error: Timeout**

```
Response did not arrive within the allocated time.
```

**Solution:**
1. Increase timeout value in boto3 config
2. Check network connectivity
3. Verify region is accessible
4. Try different region temporarily

---

## **PRODUCTION CHECKLIST**

Before deploying to production:

- [ ] Models enabled in Bedrock console
- [ ] IAM permissions configured
- [ ] CloudWatch monitoring enabled
- [ ] Error handling implemented
- [ ] Retry logic with exponential backoff
- [ ] Rate limiting implemented
- [ ] Cost alerts configured
- [ ] Security audit completed
- [ ] Load testing done
- [ ] Logging configured
- [ ] Runbook created for common issues
- [ ] On-call procedures documented

---

## **SUPPORT & RESOURCES**

- **AWS Bedrock Docs:** https://docs.aws.amazon.com/bedrock/
- **Anthropic Claude Docs:** https://docs.anthropic.com/
- **AWS Support:** https://console.aws.amazon.com/support/
- **Bedrock Pricing:** https://aws.amazon.com/bedrock/pricing/

---

## **SUMMARY**

| Aspect | Details |
|---|---|
| **Primary Model** | Claude 3.5 Sonnet (us.anthropic.claude-3-5-sonnet-20241022-v2:0) |
| **Embeddings Model** | Titan Text Embeddings v2 (amazon.titan-embed-text-v2:0) |
| **Region** | us-east-1 |
| **API** | Converse API (unified, model-agnostic) |
| **Auth** | IAM-based (no API keys needed) |
| **Encryption** | TLS in-transit, AWS managed at-rest |
| **Pricing** | $3/1M input, $15/1M output tokens |
| **Estimated Monthly Cost** | $2-3 (POC), scales with usage |
| **Status** | ✅ Production Ready |

---

**For questions or issues with Bedrock configuration, refer to the troubleshooting section or contact AWS Support.**
