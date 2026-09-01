#!/usr/bin/env python3
"""
Optimized Performance Testing Suite - Task 4.5
Captures comprehensive metrics with failure categorization and optimization analysis.
"""

import asyncio
import json
import logging
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import httpx
from dotenv import load_dotenv

# Load environment
load_dotenv()
os.environ['BEDROCK_MODEL_ID'] = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-haiku-4-5-20251001-v2:0')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent
REPORTS_DIR = PROJECT_ROOT / "performance_reports"
REPORTS_DIR.mkdir(exist_ok=True)


class FailureAnalyzer:
    """Analyzes and categorizes HTTP response failures."""

    @staticmethod
    def categorize_failure(status_code: int, response_text: str = "", latency_ms: float = 0) -> str:
        """Categorize a failure based on HTTP status and response."""
        if status_code == 400:
            if "validation" in response_text.lower() or "too short" in response_text.lower():
                return "validation_error"
            return "bad_request"
        elif status_code == 429:
            return "throttling"
        elif status_code in (502, 504):
            return "gateway_timeout"
        elif status_code == 503:
            return "service_unavailable"
        elif status_code == 500:
            return "server_error"
        elif status_code == 401 or status_code == 403:
            return "auth_error"
        elif status_code >= 500:
            return "server_error"
        elif latency_ms > 30000:
            return "client_timeout"
        else:
            return "unknown"


class PerformanceMetrics:
    """Collects and analyzes performance test metrics."""

    def __init__(self):
        self.requests = []
        self.start_time = None
        self.end_time = None
        self.failure_categories = {}
        self.response_times = []
        self.successful_count = 0
        self.failed_count = 0

    def add_request(self, method: str, endpoint: str, status_code: int, latency_ms: float, response_text: str = ""):
        """Record a request."""
        category = "success" if status_code < 400 else FailureAnalyzer.categorize_failure(status_code, response_text, latency_ms)

        request_data = {
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "category": category,
            "timestamp": datetime.now().isoformat()
        }
        self.requests.append(request_data)
        self.response_times.append(latency_ms)

        if status_code < 400:
            self.successful_count += 1
        else:
            self.failed_count += 1

        # Track failure categories
        if category not in self.failure_categories:
            self.failure_categories[category] = 0
        self.failure_categories[category] += 1

    def get_summary(self) -> dict:
        """Get performance summary statistics."""
        total_requests = len(self.requests)
        if total_requests == 0:
            return {}

        success_rate = (self.successful_count / total_requests) * 100

        # Calculate percentiles
        sorted_times = sorted(self.response_times)
        p50_idx = int(total_requests * 0.5)
        p95_idx = int(total_requests * 0.95)
        p99_idx = int(total_requests * 0.99)

        return {
            "total_requests": total_requests,
            "successful_requests": self.successful_count,
            "failed_requests": self.failed_count,
            "success_rate_percent": success_rate,
            "throughput_rps": total_requests / (self.end_time - self.start_time) if self.end_time and self.start_time else 0,
            "response_times": {
                "min_ms": min(self.response_times),
                "max_ms": max(self.response_times),
                "avg_ms": sum(self.response_times) / len(self.response_times),
                "p50_ms": sorted_times[p50_idx] if p50_idx < len(sorted_times) else 0,
                "p95_ms": sorted_times[p95_idx] if p95_idx < len(sorted_times) else 0,
                "p99_ms": sorted_times[p99_idx] if p99_idx < len(sorted_times) else 0,
            },
            "failure_breakdown": self.failure_categories
        }


async def run_load_test(
    num_users: int = 100,
    duration_seconds: int = 60,
    base_url: str = "http://localhost:8000"
) -> PerformanceMetrics:
    """Run load test with specified concurrency and duration."""
    metrics = PerformanceMetrics()
    metrics.start_time = time.time()

    # First, authenticate to get a token
    auth_token = None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            auth_response = await client.post(
                f"{base_url}/api/auth/login",
                json={
                    "email": "testuser@example.com",
                    "password": "TestPassword123!"
                }
            )
            if auth_response.status_code == 200:
                auth_token = auth_response.json().get("access_token")
                log.info(f"Authentication successful, token: {auth_token[:20]}...")
            else:
                log.warning(f"Authentication failed: {auth_response.status_code}")
    except Exception as e:
        log.error(f"Failed to authenticate: {e}")
        return metrics

    if not auth_token:
        log.error("Could not obtain authentication token")
        return metrics

    # Generate job descriptions for testing
    test_job_descriptions = [
        "Senior Python Engineer with 5+ years experience in Django and FastAPI. Skills: Python, PostgreSQL, Docker. Salary: 120k-160k",
        "Full Stack Developer (React/Node.js) for fintech startup. Requirements: 3+ years, TypeScript, testing. 100k-140k",
        "DevOps Engineer - AWS/Kubernetes expertise needed. Infrastructure automation, CI/CD. 110k-150k",
        "Data Engineer for ML platform. PySpark, data modeling, big data. 3+ years. 130k-170k",
        "Software Architect - 10+ years experience. System design, microservices, cloud. 150k-200k"
    ]

    # Create concurrent tasks
    async def make_request(client: httpx.AsyncClient, job_description: str) -> None:
        start = time.time()
        try:
            response = await client.post(
                f"{base_url}/api/jobs/parse",
                json={"job_description": job_description},
                headers={"Authorization": f"Bearer {auth_token}"},
                timeout=45.0
            )
            latency_ms = (time.time() - start) * 1000
            response_text = response.text[:200] if response.text else ""
            metrics.add_request("POST", "/api/jobs/parse", response.status_code, latency_ms, response_text)

            if response.status_code < 400:
                log.info(f"✓ Success ({response.status_code}): {latency_ms:.0f}ms")
            else:
                log.warning(f"✗ Failed ({response.status_code}): {latency_ms:.0f}ms - {response.text[:100]}")
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start) * 1000
            metrics.add_request("POST", "/api/jobs/parse", 504, latency_ms, "timeout")
            log.warning(f"✗ Timeout: {latency_ms:.0f}ms")
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            metrics.add_request("POST", "/api/jobs/parse", 500, latency_ms, str(e))
            log.error(f"✗ Error: {e}")

    # Run load test
    log.info(f"Starting load test: {num_users} concurrent users, {duration_seconds}s duration")
    log.info("="*80)

    end_time = time.time() + duration_seconds
    job_idx = 0

    async with httpx.AsyncClient(timeout=45.0) as client:
        tasks = []
        while time.time() < end_time:
            # Create new concurrent users up to the limit
            while len(tasks) < num_users and time.time() < end_time:
                job_desc = test_job_descriptions[job_idx % len(test_job_descriptions)]
                task = asyncio.create_task(make_request(client, job_desc))
                tasks.append(task)
                job_idx += 1
                await asyncio.sleep(0.05)  # Stagger request startup

            # Wait for some tasks to complete
            if tasks:
                done, pending = await asyncio.wait(tasks, timeout=1.0, return_when=asyncio.FIRST_COMPLETED)
                tasks = list(pending)

    metrics.end_time = time.time()
    return metrics


async def run_optimized_load_test():
    """Run the complete optimized load test suite."""
    print("\n" + "*"*80)
    print("*" + " BEDROCK POC - OPTIMIZED PERFORMANCE TEST ".center(78) + "*")
    print("*"*80 + "\n")

    log.info("Prerequisite checks...")

    # Check API server
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                log.info("✓ API server: OK")
            else:
                log.error("✗ API server not ready")
                return False
    except Exception as e:
        log.error(f"✗ API server check failed: {e}")
        return False

    # Run load test
    log.info("\n" + "="*80)
    log.info("OPTIMIZED LOAD TEST (100 Concurrent Users, 60 seconds)")
    log.info("="*80 + "\n")

    metrics = await run_load_test(num_users=100, duration_seconds=60)
    summary = metrics.get_summary()

    # Print results
    print("\n" + "="*80)
    print("PERFORMANCE TEST RESULTS")
    print("="*80)
    print(f"\nTotal Requests:        {summary.get('total_requests', 0)}")
    print(f"Successful Requests:   {summary.get('successful_requests', 0)}")
    print(f"Failed Requests:       {summary.get('failed_requests', 0)}")
    print(f"Success Rate:          {summary.get('success_rate_percent', 0):.2f}%")
    print(f"Throughput:            {summary.get('throughput_rps', 0):.2f} req/sec")

    print("\nResponse Times:")
    response_times = summary.get('response_times', {})
    print(f"  Min:                 {response_times.get('min_ms', 0):.0f}ms")
    print(f"  Max:                 {response_times.get('max_ms', 0):.0f}ms")
    print(f"  Average:             {response_times.get('avg_ms', 0):.0f}ms")
    print(f"  P50 (Median):        {response_times.get('p50_ms', 0):.0f}ms")
    print(f"  P95:                 {response_times.get('p95_ms', 0):.0f}ms")
    print(f"  P99:                 {response_times.get('p99_ms', 0):.0f}ms")

    print("\nFailure Breakdown:")
    failure_breakdown = summary.get('failure_breakdown', {})
    for category, count in sorted(failure_breakdown.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / summary.get('total_requests', 1)) * 100
        print(f"  {category:20s}: {count:5d} ({percentage:6.2f}%)")

    # Save detailed report
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_config": {
            "concurrent_users": 100,
            "duration_seconds": 60,
            "base_url": "http://localhost:8000"
        },
        "summary": summary,
        "requests": metrics.requests[:100]  # Save first 100 detailed requests
    }

    report_file = REPORTS_DIR / f"optimized_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    log.info(f"\nReport saved to: {report_file}")
    print("\n" + "="*80)

    return summary.get('success_rate_percent', 0) > 10  # Success if >10% pass rate


def main():
    """Main entry point."""
    try:
        success = asyncio.run(run_optimized_load_test())
        return 0 if success else 1
    except KeyboardInterrupt:
        log.info("Test interrupted by user")
        return 1
    except Exception as e:
        log.error(f"Test failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
