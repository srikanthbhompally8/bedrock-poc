#!/usr/bin/env python3
"""List available Bedrock inference profiles."""

import boto3
from botocore.exceptions import ClientError

def list_inference_profiles():
    """List available inference profiles."""

    region = "us-east-1"

    print(f"\n{'='*80}")
    print(f"LISTING BEDROCK INFERENCE PROFILES - Region: {region}")
    print(f"{'='*80}\n")

    try:
        client = boto3.client("bedrock", region_name=region)

        # List inference profiles
        response = client.list_inference_profiles()

        profiles = response.get('inferenceProfileSummaries', [])

        if profiles:
            print(f"Found {len(profiles)} inference profiles:\n")
            for profile in profiles:
                print(f"Profile ID: {profile.get('inferenceProfileId', 'N/A')}")
                print(f"Name: {profile.get('inferenceProfileName', 'N/A')}")
                print(f"Status: {profile.get('inferenceProfileStatus', 'N/A')}")
                print(f"Models: {profile.get('models', [])}")
                print()

            # Show the first profile's full ID for testing
            first_profile = profiles[0]
            profile_id = first_profile.get('inferenceProfileId', '')
            if profile_id:
                print(f"\n→ Use this model ID for configuration:")
                print(f"  {profile_id}")
        else:
            print("No inference profiles found.")

    except Exception as e:
        print(f"Error: {e}")
        print("\nTrying alternative approach...")

        try:
            # Alternative: try with regional inference profile prefix
            print("\nTrying regional inference profile format:")
            test_ids = [
                "us.anthropic.claude-sonnet-4-20250514-v1:0",
                "us.anthropic.claude-sonnet-4-20250514-v1",
            ]

            client = boto3.client("bedrock-runtime", region_name=region)

            for test_id in test_ids:
                print(f"\nTesting: {test_id}")
                try:
                    response = client.converse(
                        modelId=test_id,
                        messages=[{"role": "user", "content": [{"text": "test"}]}],
                        inferenceConfig={"maxTokens": 10}
                    )
                    print(f"  ✓ SUCCESS - This profile works!")
                    break
                except Exception as e:
                    print(f"  ✗ Failed: {str(e)[:100]}")

        except Exception as e2:
            print(f"Alternative approach failed: {e2}")

if __name__ == "__main__":
    list_inference_profiles()
