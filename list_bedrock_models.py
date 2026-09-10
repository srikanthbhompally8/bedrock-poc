#!/usr/bin/env python3
"""List all available Bedrock models in the account."""

import boto3
from botocore.exceptions import ClientError

def list_bedrock_models():
    """List all available Bedrock models."""

    region = "us-east-1"

    print(f"\n{'='*80}")
    print(f"LISTING AVAILABLE BEDROCK MODELS - Region: {region}")
    print(f"{'='*80}\n")

    try:
        # Use bedrock (not bedrock-runtime) to list available models
        client = boto3.client("bedrock", region_name=region)

        # List available models
        response = client.list_foundation_models()

        print(f"Found {len(response['modelSummaries'])} models:\n")

        # Filter for Claude models
        claude_models = [m for m in response['modelSummaries'] if 'claude' in m['modelId'].lower()]

        if claude_models:
            print("CLAUDE MODELS AVAILABLE:")
            for model in claude_models:
                print(f"  - {model['modelId']}")
                print(f"    Provider: {model['provider']}")
                print(f"    Input tokens: {model.get('inputTokenCount', 'N/A')}")
                print(f"    Output tokens: {model.get('outputTokenCount', 'N/A')}")
                print()
        else:
            print("No Claude models found.")
            print("\nAll available models:")
            for model in response['modelSummaries']:
                print(f"  - {model['modelId']} ({model['provider']})")

    except ClientError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    list_bedrock_models()
