#!/usr/bin/env python3
"""Wrapper to run performance tests with correct Bedrock model configuration."""

import os
import sys

# Set environment variable BEFORE importing anything
os.environ['BEDROCK_MODEL_ID'] = 'anthropic.claude-haiku-4-5-20251001-v2:0'

# Now import and run
if __name__ == "__main__":
    from run_complete_performance_tests import main
    sys.exit(main())
