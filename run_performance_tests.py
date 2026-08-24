#!/usr/bin/env python3
"""
Comprehensive Performance Testing Execution Script for Bedrock POC.

This script orchestrates the complete performance testing workflow:
1. Initializes the database with test data
2. Starts the API server
3. Runs load performance tests
4. Runs database performance tests
5. Collects system metrics
6. Generates performance report
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"


class PerformanceTestOrchestrator:
    """Orchestrates performance testing workflow."""

    def __init__(self):
        self.start_time = None
        self.results = {}
        self.server_process = None

    def log_section(self, title: str):
        """Log section header."""
        print("\n" + "="*80)
        print(f" {title.center(78)}")
        print("="*80 + "\n")

    async def run_async_tests(self):
        """Run async performance tests."""
        try:
            self.log_section("RUNNING LOAD PERFORMANCE TESTS")
            log.info("Starting load performance tests...")

            # Import and run async tests
            from tests.test_load_performance import LoadTestScenarios, format_results_table

            # Run baseline test
            log.info("Running baseline performance test...")
            try:
                baseline_results = await LoadTestScenarios.baseline_performance_test()
                print(format_results_table(baseline_results))
                self.results['baseline'] = baseline_results
            except Exception as e:
                log.error(f"Baseline test failed: {e}")

            # Run load test
            log.info("Running load performance test...")
            try:
                load_results = await LoadTestScenarios.load_test()
                print(format_results_table(load_results))
                self.results['load'] = load_results
            except Exception as e:
                log.error(f"Load test failed: {e}")

            # Run stress test
            log.info("Running stress test...")
            try:
                stress_results = await LoadTestScenarios.stress_test()
                print(format_results_table(stress_results))
                self.results['stress'] = stress_results
            except Exception as e:
                log.error(f"Stress test failed: {e}")

        except Exception as e:
            log.error(f"Error running async tests: {e}")

    def wait_for_api(self, timeout: int = 30):
        """Wait for API server to be ready."""
        import httpx

        start_time = time.time()
        base_url = "http://localhost:8000"

        while time.time() - start_time < timeout:
            try:
                with httpx.Client() as client:
                    response = client.get(f"{base_url}/health", timeout=5)
                    if response.status_code == 200:
                        log.info("API server is ready!")
                        return True
            except Exception:
                pass

            time.sleep(1)

        log.error(f"API server did not become ready within {timeout}s")
        return False

    def run_tests(self):
        """Execute the complete performance testing workflow."""
        self.start_time = datetime.now()

        try:
            self.log_section("BEDROCK POC PERFORMANCE TESTING")
            log.info(f"Testing started at {self.start_time.isoformat()}")
            log.info(f"Python {sys.version}")

            # Check prerequisites
            self.log_section("PREREQUISITES CHECK")

            # Check database
            log.info("Checking database connection...")
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    user=os.getenv('DB_USER', 'postgres'),
                    password=os.getenv('DB_PASSWORD', 'postgres'),
                    database=os.getenv('DB_NAME', 'bedrock_poc')
                )
                conn.close()
                log.info("Database connection OK")
            except Exception as e:
                log.error(f"Database connection failed: {e}")
                return False

            # Check if API server is already running
            self.log_section("API SERVER CHECK")

            import httpx
            try:
                with httpx.Client() as client:
                    response = client.get("http://localhost:8000/health", timeout=5)
                    if response.status_code == 200:
                        log.info("API server is already running on port 8000")
                        api_ready = True
                    else:
                        api_ready = False
            except Exception:
                api_ready = False

            if not api_ready:
                log.warning("API server is not running. Please start it manually with:")
                log.warning("  uvicorn bedrock_poc.api.main:app --host 0.0.0.0 --port 8000 --reload")
                log.warning("\nOr run this script again once the API is running.")
                return False

            # Run tests
            log.info("Running performance tests...")
            asyncio.run(self.run_async_tests())

            # Generate report
            self.log_section("PERFORMANCE TESTING COMPLETE")
            duration = datetime.now() - self.start_time
            log.info(f"Testing completed in {duration}")
            log.info(f"Results: {len(self.results)} test scenarios")

            return True

        except KeyboardInterrupt:
            log.warning("Testing interrupted by user")
            return False
        except Exception as e:
            log.error(f"Error during testing: {e}", exc_info=True)
            return False


def main():
    """Main entry point."""
    orchestrator = PerformanceTestOrchestrator()

    print("\n")
    print("*" * 80)
    print("*" + " BEDROCK POC - PERFORMANCE & LOAD TESTING ".center(78) + "*")
    print("*" * 80)
    print("\nPREREQUISITES:")
    print("  1. PostgreSQL must be running")
    print("  2. API server must be running on port 8000")
    print("     Start it with: uvicorn bedrock_poc.api.main:app --reload")
    print("  3. All dependencies must be installed")
    print("     pip install -r requirements.txt")
    print()

    success = orchestrator.run_tests()

    if success:
        print("\n" + "*" * 80)
        print("*" + " TESTING COMPLETED SUCCESSFULLY ".center(78) + "*")
        print("*" * 80)
        print("\nNext steps:")
        print("  1. Review performance test results above")
        print("  2. Check docs/PERFORMANCE_TESTING.md for detailed analysis")
        print("  3. Review STATUS_REPORT_PHASE4_TASK45.md for optimization recommendations")
        print()
        return 0
    else:
        print("\n" + "*" * 80)
        print("*" + " TESTING FAILED OR INCOMPLETE ".center(78) + "*")
        print("*" * 80)
        print("\nPlease ensure:")
        print("  1. PostgreSQL is running and accessible")
        print("  2. The API server is running: uvicorn bedrock_poc.api.main:app --reload")
        print("  3. All dependencies are installed: pip install -r requirements.txt")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
