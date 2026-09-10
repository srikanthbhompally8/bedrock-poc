#!/usr/bin/env python3
"""Test Bedrock connectivity and available models."""

import boto3
import json
from botocore.exceptions import ClientError

def test_bedrock_models():
    """Test available Bedrock models in current region."""

    region = "us-east-1"
    client = boto3.client("bedrock-runtime", region_name=region)

    print(f"\n{'='*80}")
    print(f"BEDROCK MODEL VALIDATION - Region: {region}")
    print(f"{'='*80}\n")

    # List of models to test - CONFIRMED AVAILABLE INFERENCE PROFILES
    models_to_test = [
        # ✓ CONFIRMED AVAILABLE - Using inference profile IDs (with us. prefix)
        "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    ]

    print("Testing model availability:\n")

    available_models = []

    for model_id in models_to_test:
        print(f"Testing: {model_id}")
        try:
            # Try a simple inference to validate model
            response = client.converse(
                modelId=model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": "Hello"}]
                    }
                ],
                inferenceConfig={"maxTokens": 10}
            )
            print(f"  ✓ AVAILABLE - Inference successful")
            available_models.append(model_id)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            print(f"  ✗ NOT AVAILABLE - {error_code}: {error_msg}")
        except Exception as e:
            print(f"  ✗ ERROR - {str(e)}")
        print()

    print(f"{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}\n")

    if available_models:
        print(f"✓ {len(available_models)} Available Model(s):\n")
        for model in available_models:
            print(f"  - {model}")
        print(f"\n→ Recommended for use: {available_models[0]}")
    else:
        print("✗ No models available. Check AWS credentials and IAM permissions.")

    return available_models

if __name__ == "__main__":
    import sys
    try:
        models = test_bedrock_models()
        sys.exit(0 if models else 1)
    except Exception as e:
        print(f"\n✗ Error testing Bedrock: {e}")
        sys.exit(1)
