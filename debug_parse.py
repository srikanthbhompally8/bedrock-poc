"""Debug script to test resume parsing step by step."""

import json
import logging
from bedrock_poc import client as bedrock
from bedrock_poc import use_cases

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

def test_parse_resume():
    """Test resume parsing with debugging output."""

    # Create test resume
    test_resume = """
    John Doe
    john@example.com
    555-123-4567

    Senior Software Engineer with 5 years of experience

    Skills: Python, AWS, Docker, Kubernetes

    Experience:
    - Senior Engineer at Tech Corp (2020-Present)
      Led cloud infrastructure projects

    Education:
    - B.S. Computer Science, State University, 2018
    """

    print("=" * 60)
    print("RESUME PARSING DEBUG TEST")
    print("=" * 60)

    # Step 1: Build client
    print("\n[1] Building Bedrock client...")
    try:
        client = bedrock.build_client()
        print("✅ Client built successfully")
    except Exception as e:
        print(f"❌ Failed to build client: {e}")
        return

    # Step 2: Test parse_resume
    print("\n[2] Parsing resume...")
    try:
        result = use_cases.parse_resume(client, test_resume)
        print("✅ Resume parsed successfully!")
        print(f"\n   Name: {result.full_name}")
        print(f"   Email: {result.email}")
        print(f"   Phone: {result.phone}")
        print(f"   Skills: {', '.join(result.skills)}")
        print(f"   Experience: {len(result.experience)} entries")
        print(f"   Education: {len(result.education)} entries")

        # Step 3: Show JSON output
        print("\n[3] Full JSON output:")
        print(json.dumps(result.model_dump(), indent=2))

    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        print(f"\nError type: {type(e).__name__}")
        print(f"Error details: {str(e)}")

if __name__ == "__main__":
    test_parse_resume()
