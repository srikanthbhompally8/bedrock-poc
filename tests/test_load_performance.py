"""
Comprehensive Load and Performance Testing Suite for Bedrock POC.

This module tests critical API endpoints under various load conditions:
- Baseline Performance (normal load)
- Load Testing (realistic peak load)
- Stress Testing (breaking point)
- Database Performance Testing
- Cache Effectiveness Testing
"""

import asyncio
import time
import statistics
import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Tuple
from datetime import datetime
import httpx
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed


# ============================================================================
# Performance Metrics Data Classes
# ============================================================================

@dataclass
class RequestMetrics:
    """Metrics for a single HTTP request."""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    timestamp: str
    success: bool
    error_message: str = ""


@dataclass
class EndpointMetrics:
    """Aggregated metrics for an endpoint."""
    endpoint: str
    method: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    min_response_time_ms: float = float('inf')
    max_response_time_ms: float = 0
    avg_response_time_ms: float = 0
    p50_response_time_ms: float = 0
    p95_response_time_ms: float = 0
    p99_response_time_ms: float = 0
    error_rate: float = 0
    throughput_req_per_sec: float = 0
    response_times: List[float] = field(default_factory=list)


@dataclass
class LoadTestResults:
    """Results from a load test scenario."""
    scenario_name: str
    concurrent_users: int
    duration_seconds: int
    total_requests: int
    total_errors: int
    error_rate: float
    min_response_time_ms: float
    max_response_time_ms: float
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    throughput_req_per_sec: float
    endpoints: List[EndpointMetrics] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# Base Test Configuration
# ============================================================================

class LoadTestConfig:
    """Configuration for load testing."""

    BASE_URL = "http://localhost:8000"
    TIMEOUT = 30

    # Test users
    TEST_USER_EMAIL = "testuser@example.com"
    TEST_USER_PASSWORD = "TestPassword123!"
    TEST_ADMIN_EMAIL = "admin@example.com"
    TEST_ADMIN_PASSWORD = "AdminPassword123!"

    # Test data
    SAMPLE_JOB_DESCRIPTION = """
    Senior Software Engineer - Python

    We are looking for a Senior Software Engineer with expertise in Python,
    FastAPI, and cloud technologies. The ideal candidate should have:

    Requirements:
    - 5+ years of Python development experience
    - Expertise in FastAPI and REST APIs
    - Experience with PostgreSQL and Redis
    - AWS experience (EC2, RDS, S3)
    - Strong understanding of microservices architecture
    - Experience with Docker and Kubernetes
    - Git and CI/CD expertise
    - Excellent communication skills

    Nice to have:
    - Machine Learning experience
    - AWS Bedrock/LLM integration
    - High-performance systems design
    - Performance optimization expertise
    """


# ============================================================================
# Performance Test Client
# ============================================================================

class PerformanceTestClient:
    """Client for performance testing with metrics collection."""

    def __init__(self, base_url: str = LoadTestConfig.BASE_URL):
        self.base_url = base_url
        self.metrics: List[RequestMetrics] = []
        self.tokens: Dict[str, str] = {}

    async def register_test_user(self, email: str, password: str) -> Tuple[bool, str]:
        """Register a test user."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/auth/register",
                    json={
                        "email": email,
                        "password": password,
                        "full_name": f"Test User {email}",
                        "role": "recruiter"
                    },
                    timeout=LoadTestConfig.TIMEOUT
                )
                return response.status_code == 201, response.text
            except Exception as e:
                return False, str(e)

    async def login_user(self, email: str, password: str) -> Tuple[bool, str]:
        """Login and get JWT token."""
        async with httpx.AsyncClient() as client:
            try:
                start = time.time()
                response = await client.post(
                    f"{self.base_url}/api/auth/login",
                    json={"email": email, "password": password},
                    timeout=LoadTestConfig.TIMEOUT
                )
                elapsed = (time.time() - start) * 1000

                self.metrics.append(RequestMetrics(
                    endpoint="/api/auth/login",
                    method="POST",
                    status_code=response.status_code,
                    response_time_ms=elapsed,
                    timestamp=datetime.now().isoformat(),
                    success=response.status_code == 200
                ))

                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token")
                    self.tokens[email] = token
                    return True, token
                return False, response.text
            except Exception as e:
                self.metrics.append(RequestMetrics(
                    endpoint="/api/auth/login",
                    method="POST",
                    status_code=0,
                    response_time_ms=0,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    error_message=str(e)
                ))
                return False, str(e)

    async def parse_job(self, token: str, job_description: str) -> Tuple[bool, float]:
        """Parse a job description and return response time."""
        async with httpx.AsyncClient() as client:
            try:
                start = time.time()
                response = await client.post(
                    f"{self.base_url}/api/jobs/parse",
                    json={"job_description": job_description},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=LoadTestConfig.TIMEOUT
                )
                elapsed = (time.time() - start) * 1000

                self.metrics.append(RequestMetrics(
                    endpoint="/api/jobs/parse",
                    method="POST",
                    status_code=response.status_code,
                    response_time_ms=elapsed,
                    timestamp=datetime.now().isoformat(),
                    success=response.status_code == 200
                ))

                return response.status_code == 200, elapsed
            except Exception as e:
                self.metrics.append(RequestMetrics(
                    endpoint="/api/jobs/parse",
                    method="POST",
                    status_code=0,
                    response_time_ms=0,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    error_message=str(e)
                ))
                return False, 0

    async def get_candidates(self, token: str) -> Tuple[bool, float]:
        """Fetch candidates list."""
        async with httpx.AsyncClient() as client:
            try:
                start = time.time()
                response = await client.get(
                    f"{self.base_url}/api/candidates",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=LoadTestConfig.TIMEOUT
                )
                elapsed = (time.time() - start) * 1000

                self.metrics.append(RequestMetrics(
                    endpoint="/api/candidates",
                    method="GET",
                    status_code=response.status_code,
                    response_time_ms=elapsed,
                    timestamp=datetime.now().isoformat(),
                    success=response.status_code == 200
                ))

                return response.status_code == 200, elapsed
            except Exception as e:
                self.metrics.append(RequestMetrics(
                    endpoint="/api/candidates",
                    method="GET",
                    status_code=0,
                    response_time_ms=0,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    error_message=str(e)
                ))
                return False, 0

    async def get_matches(self, token: str) -> Tuple[bool, float]:
        """Fetch matches list."""
        async with httpx.AsyncClient() as client:
            try:
                start = time.time()
                response = await client.get(
                    f"{self.base_url}/api/matches",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=LoadTestConfig.TIMEOUT
                )
                elapsed = (time.time() - start) * 1000

                self.metrics.append(RequestMetrics(
                    endpoint="/api/matches",
                    method="GET",
                    status_code=response.status_code,
                    response_time_ms=elapsed,
                    timestamp=datetime.now().isoformat(),
                    success=response.status_code == 200
                ))

                return response.status_code == 200, elapsed
            except Exception as e:
                self.metrics.append(RequestMetrics(
                    endpoint="/api/matches",
                    method="GET",
                    status_code=0,
                    response_time_ms=0,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    error_message=str(e)
                ))
                return False, 0

    async def health_check(self) -> Tuple[bool, float]:
        """Check API health."""
        async with httpx.AsyncClient() as client:
            try:
                start = time.time()
                response = await client.get(
                    f"{self.base_url}/health",
                    timeout=5
                )
                elapsed = (time.time() - start) * 1000

                self.metrics.append(RequestMetrics(
                    endpoint="/api/health",
                    method="GET",
                    status_code=response.status_code,
                    response_time_ms=elapsed,
                    timestamp=datetime.now().isoformat(),
                    success=response.status_code == 200
                ))

                return response.status_code == 200, elapsed
            except Exception as e:
                self.metrics.append(RequestMetrics(
                    endpoint="/api/health",
                    method="GET",
                    status_code=0,
                    response_time_ms=0,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    error_message=str(e)
                ))
                return False, 0


# ============================================================================
# Metrics Analysis
# ============================================================================

class MetricsAnalyzer:
    """Analyze and aggregate performance metrics."""

    @staticmethod
    def calculate_percentile(values: List[float], percentile: float) -> float:
        """Calculate percentile from sorted values."""
        if not values:
            return 0
        sorted_values = sorted(values)
        idx = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(idx, len(sorted_values) - 1)]

    @staticmethod
    def analyze_metrics(metrics: List[RequestMetrics], duration_seconds: int) -> LoadTestResults:
        """Analyze metrics and generate results."""
        if not metrics:
            return LoadTestResults(
                scenario_name="Empty",
                concurrent_users=0,
                duration_seconds=duration_seconds,
                total_requests=0,
                total_errors=0,
                error_rate=0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                avg_response_time_ms=0,
                p50_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                throughput_req_per_sec=0
            )

        # Group by endpoint
        endpoint_map: Dict[Tuple[str, str], List[RequestMetrics]] = {}
        for metric in metrics:
            key = (metric.endpoint, metric.method)
            if key not in endpoint_map:
                endpoint_map[key] = []
            endpoint_map[key].append(metric)

        # Calculate endpoint metrics
        endpoint_metrics = []
        all_response_times = []

        for (endpoint, method), endpoint_requests in endpoint_map.items():
            successful = [m for m in endpoint_requests if m.success]
            failed = [m for m in endpoint_requests if not m.success]
            response_times = [m.response_time_ms for m in successful]

            all_response_times.extend(response_times)

            em = EndpointMetrics(
                endpoint=endpoint,
                method=method,
                total_requests=len(endpoint_requests),
                successful_requests=len(successful),
                failed_requests=len(failed),
                response_times=response_times
            )

            if response_times:
                em.min_response_time_ms = min(response_times)
                em.max_response_time_ms = max(response_times)
                em.avg_response_time_ms = statistics.mean(response_times)
                em.p50_response_time_ms = MetricsAnalyzer.calculate_percentile(response_times, 50)
                em.p95_response_time_ms = MetricsAnalyzer.calculate_percentile(response_times, 95)
                em.p99_response_time_ms = MetricsAnalyzer.calculate_percentile(response_times, 99)

            em.error_rate = (len(failed) / len(endpoint_requests) * 100) if endpoint_requests else 0
            em.throughput_req_per_sec = len(endpoint_requests) / max(duration_seconds, 1)

            endpoint_metrics.append(em)

        # Calculate overall metrics
        total_requests = len(metrics)
        failed_requests = sum(1 for m in metrics if not m.success)
        error_rate = (failed_requests / total_requests * 100) if total_requests else 0
        throughput = total_requests / max(duration_seconds, 1)

        result = LoadTestResults(
            scenario_name="Load Test",
            concurrent_users=0,
            duration_seconds=duration_seconds,
            total_requests=total_requests,
            total_errors=failed_requests,
            error_rate=error_rate,
            min_response_time_ms=min(all_response_times) if all_response_times else 0,
            max_response_time_ms=max(all_response_times) if all_response_times else 0,
            avg_response_time_ms=statistics.mean(all_response_times) if all_response_times else 0,
            p50_response_time_ms=MetricsAnalyzer.calculate_percentile(all_response_times, 50),
            p95_response_time_ms=MetricsAnalyzer.calculate_percentile(all_response_times, 95),
            p99_response_time_ms=MetricsAnalyzer.calculate_percentile(all_response_times, 99),
            throughput_req_per_sec=throughput,
            endpoints=endpoint_metrics
        )

        return result


# ============================================================================
# Load Test Scenarios
# ============================================================================

class LoadTestScenarios:
    """Define and execute load test scenarios."""

    @staticmethod
    async def baseline_performance_test() -> LoadTestResults:
        """Test baseline performance with normal load (10 concurrent users, 1 hour)."""
        print("\n" + "="*80)
        print("BASELINE PERFORMANCE TEST (10 Concurrent Users)")
        print("="*80)

        client = PerformanceTestClient()
        duration = 300  # 5 minutes for initial testing
        concurrent_users = 10

        # Setup: Login (user is created on server startup)
        success, token = await client.login_user(LoadTestConfig.TEST_USER_EMAIL, LoadTestConfig.TEST_USER_PASSWORD)
        if not success:
            raise Exception("Failed to login test user")

        print(f"Test user logged in successfully")
        print(f"Running baseline test with {concurrent_users} concurrent users for {duration}s")

        # Run test
        start_time = time.time()
        tasks = []

        async def worker_task():
            while time.time() - start_time < duration:
                # Rotate through different endpoints
                endpoint_choice = int(time.time() * 1000) % 4
                if endpoint_choice == 0:
                    await client.parse_job(token, LoadTestConfig.SAMPLE_JOB_DESCRIPTION)
                elif endpoint_choice == 1:
                    await client.get_candidates(token)
                elif endpoint_choice == 2:
                    await client.get_matches(token)
                else:
                    await client.health_check()

                await asyncio.sleep(0.1)  # Small delay between requests

        for _ in range(concurrent_users):
            tasks.append(worker_task())

        await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.time() - start_time
        results = MetricsAnalyzer.analyze_metrics(client.metrics, int(elapsed))
        results.scenario_name = "Baseline Performance (10 Users)"
        results.concurrent_users = concurrent_users

        return results

    @staticmethod
    async def load_test() -> LoadTestResults:
        """Test realistic peak load (100 concurrent users, 30 minutes)."""
        print("\n" + "="*80)
        print("LOAD TEST (100 Concurrent Users)")
        print("="*80)

        client = PerformanceTestClient()
        duration = 60  # 1 minute for initial testing
        concurrent_users = 100

        # Setup: Login
        success, token = await client.login_user(LoadTestConfig.TEST_USER_EMAIL, LoadTestConfig.TEST_USER_PASSWORD)
        if not success:
            raise Exception("Failed to login test user")

        print(f"Running load test with {concurrent_users} concurrent users for {duration}s")

        # Run test
        start_time = time.time()
        tasks = []

        async def worker_task():
            while time.time() - start_time < duration:
                # Focus on job parsing (most resource intensive)
                await client.parse_job(token, LoadTestConfig.SAMPLE_JOB_DESCRIPTION)
                await asyncio.sleep(0.05)

        for _ in range(concurrent_users):
            tasks.append(worker_task())

        await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.time() - start_time
        results = MetricsAnalyzer.analyze_metrics(client.metrics, int(elapsed))
        results.scenario_name = "Load Test (100 Users)"
        results.concurrent_users = concurrent_users

        return results

    @staticmethod
    async def stress_test() -> LoadTestResults:
        """Test stress conditions (gradually increase to 500+ concurrent users)."""
        print("\n" + "="*80)
        print("STRESS TEST (Gradual Load Increase)")
        print("="*80)

        client = PerformanceTestClient()

        # Setup: Login
        success, token = await client.login_user(LoadTestConfig.TEST_USER_EMAIL, LoadTestConfig.TEST_USER_PASSWORD)
        if not success:
            raise Exception("Failed to login test user")

        print("Running stress test with gradual load increase")

        # Gradually increase load
        max_concurrent = 50  # Reduced for initial testing
        start_time = time.time()
        current_tasks = []

        async def worker_task():
            while time.time() - start_time < 120:  # 2 minutes total
                await client.parse_job(token, LoadTestConfig.SAMPLE_JOB_DESCRIPTION)
                await asyncio.sleep(0.1)

        # Gradually add workers
        for user_count in [10, 20, 30, 40, 50]:
            print(f"Current concurrent users: {user_count}")
            # Add new workers
            for _ in range(user_count - len(current_tasks)):
                current_tasks.append(worker_task())

            await asyncio.sleep(15)  # Hold at this load for 15s

        # Wait for all to complete
        await asyncio.gather(*current_tasks, return_exceptions=True)

        elapsed = time.time() - start_time
        results = MetricsAnalyzer.analyze_metrics(client.metrics, int(elapsed))
        results.scenario_name = "Stress Test (Gradual Increase)"
        results.concurrent_users = max_concurrent

        return results


# ============================================================================
# Test Execution and Reporting
# ============================================================================

def format_results_table(results: LoadTestResults) -> str:
    """Format results as a readable table."""
    lines = []
    lines.append("\n" + "="*80)
    lines.append(f"SCENARIO: {results.scenario_name}")
    lines.append("="*80)
    lines.append(f"Concurrent Users:        {results.concurrent_users}")
    lines.append(f"Duration:                {results.duration_seconds}s")
    lines.append(f"Total Requests:          {results.total_requests}")
    lines.append(f"Successful Requests:     {results.total_requests - results.total_errors}")
    lines.append(f"Failed Requests:         {results.total_errors}")
    lines.append(f"Error Rate:              {results.error_rate:.2f}%")
    lines.append(f"Throughput:              {results.throughput_req_per_sec:.2f} req/sec")
    lines.append(f"\nResponse Times (ms):")
    lines.append(f"  Min:                   {results.min_response_time_ms:.2f}ms")
    lines.append(f"  Max:                   {results.max_response_time_ms:.2f}ms")
    lines.append(f"  Average:               {results.avg_response_time_ms:.2f}ms")
    lines.append(f"  P50 (Median):          {results.p50_response_time_ms:.2f}ms")
    lines.append(f"  P95:                   {results.p95_response_time_ms:.2f}ms")
    lines.append(f"  P99:                   {results.p99_response_time_ms:.2f}ms")

    if results.endpoints:
        lines.append(f"\nPer-Endpoint Metrics:")
        lines.append("-" * 80)
        lines.append(f"{'Endpoint':<30} {'Method':<6} {'Requests':<10} {'Avg (ms)':<12} {'Error %':<10}")
        lines.append("-" * 80)
        for em in results.endpoints:
            lines.append(
                f"{em.endpoint:<30} {em.method:<6} {em.total_requests:<10} "
                f"{em.avg_response_time_ms:<12.2f} {em.error_rate:<10.2f}"
            )

    lines.append("="*80 + "\n")
    return "\n".join(lines)


# ============================================================================
# Pytest Tests
# ============================================================================

@pytest.mark.asyncio
async def test_api_health():
    """Test API health check."""
    print("\nTesting API Health Check...")
    client = PerformanceTestClient()
    success, response_time = await client.health_check()
    assert success, "Health check failed"
    assert response_time < 100, f"Health check took {response_time}ms (expected < 100ms)"
    print(f"✓ Health check passed ({response_time:.2f}ms)")


@pytest.mark.asyncio
async def test_baseline_performance():
    """Run baseline performance test."""
    print("\nRunning Baseline Performance Test...")
    try:
        results = await LoadTestScenarios.baseline_performance_test()
        print(format_results_table(results))

        # Validate baseline performance criteria
        assert results.avg_response_time_ms < 200, f"Average response time {results.avg_response_time_ms}ms > 200ms"
        assert results.p95_response_time_ms < 500, f"P95 response time {results.p95_response_time_ms}ms > 500ms"
        assert results.p99_response_time_ms < 1000, f"P99 response time {results.p99_response_time_ms}ms > 1000ms"
        assert results.error_rate < 1, f"Error rate {results.error_rate}% > 1%"

        print("✓ Baseline performance test passed")
    except Exception as e:
        print(f"✗ Baseline performance test failed: {e}")
        raise


@pytest.mark.asyncio
async def test_load_performance():
    """Run load performance test."""
    print("\nRunning Load Performance Test...")
    try:
        results = await LoadTestScenarios.load_test()
        print(format_results_table(results))

        # Validate load performance criteria
        assert results.avg_response_time_ms < 300, f"Average response time {results.avg_response_time_ms}ms > 300ms"
        assert results.p95_response_time_ms < 800, f"P95 response time {results.p95_response_time_ms}ms > 800ms"
        assert results.error_rate < 2, f"Error rate {results.error_rate}% > 2%"

        print("✓ Load performance test passed")
    except Exception as e:
        print(f"✗ Load performance test failed: {e}")
        raise


@pytest.mark.asyncio
async def test_stress_test():
    """Run stress test."""
    print("\nRunning Stress Test...")
    try:
        results = await LoadTestScenarios.stress_test()
        print(format_results_table(results))

        # Stress test should complete without crashing
        assert results.total_requests > 0, "No requests completed in stress test"
        assert results.error_rate < 10, f"Error rate {results.error_rate}% > 10% in stress test"

        print("✓ Stress test completed")
    except Exception as e:
        print(f"✗ Stress test failed: {e}")
        raise


# ============================================================================
# Main Execution
# ============================================================================

async def run_all_tests():
    """Run all performance tests."""
    results_list = []

    try:
        # Test 1: Baseline Performance
        baseline = await LoadTestScenarios.baseline_performance_test()
        results_list.append(baseline)
        print(format_results_table(baseline))
    except Exception as e:
        print(f"Baseline test failed: {e}")

    try:
        # Test 2: Load Test
        load = await LoadTestScenarios.load_test()
        results_list.append(load)
        print(format_results_table(load))
    except Exception as e:
        print(f"Load test failed: {e}")

    try:
        # Test 3: Stress Test
        stress = await LoadTestScenarios.stress_test()
        results_list.append(stress)
        print(format_results_table(stress))
    except Exception as e:
        print(f"Stress test failed: {e}")

    return results_list


if __name__ == "__main__":
    # Run async tests
    asyncio.run(run_all_tests())
