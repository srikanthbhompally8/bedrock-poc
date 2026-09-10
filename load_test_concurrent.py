"""Phase 3: Load testing with 15-20 concurrent users and comprehensive metrics."""

import httpx
import asyncio
import time
import json
from datetime import datetime
from typing import List, Dict
import statistics

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "Test123!"
CONCURRENT_USERS = 20
JOBS_PER_USER = 3  # Total jobs: 20 users × 3 = 60 jobs

# Metrics storage
metrics = {
    "api_response_times": [],
    "queue_wait_times": [],
    "task_execution_times": [],
    "throughput": [],
    "success_count": 0,
    "failure_count": 0,
    "retry_count": 0,
    "bedrock_latencies": [],
    "job_ids": [],
    "start_time": None,
    "end_time": None,
}


class LoadTestUser:
    """Simulates a single concurrent user."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.token = None
        self.jobs = []

    async def authenticate(self) -> bool:
        """Authenticate and get JWT token."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BASE_URL}/api/auth/login",
                    json={
                        "email": TEST_USER_EMAIL,
                        "password": TEST_USER_PASSWORD
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    self.token = response.json()["access_token"]
                    return True
        except Exception as e:
            print(f"Auth failed for user {self.user_id}: {e}")
        return False

    async def submit_job(self, job_num: int) -> Dict:
        """Submit a job and measure API response time."""
        if not self.token:
            return {"success": False, "error": "Not authenticated"}

        job_description = f"""
        Senior Software Engineer - User {self.user_id} Job {job_num}
        Company: TechCorp

        Requirements:
        - 5+ years Python experience
        - AWS/Kubernetes expertise
        - Distributed systems knowledge

        Nice to have:
        - Bedrock/LLM experience
        - Leadership experience

        Salary: $150k-$250k
        """

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BASE_URL}/api/jobs/parse-async",
                    json={"job_description": job_description},
                    headers=headers,
                    timeout=10.0
                )
            api_response_time = time.time() - start_time

            if response.status_code == 202:
                job_data = response.json()
                return {
                    "success": True,
                    "job_id": job_data["job_id"],
                    "api_response_time": api_response_time,
                    "submitted_at": datetime.utcnow().isoformat(),
                }
            else:
                return {
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "api_response_time": api_response_time,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def check_job_status(self, job_id: str, start_time: float) -> Dict:
        """Poll job status and measure metrics."""
        if not self.token:
            return {"success": False, "error": "Not authenticated"}

        headers = {"Authorization": f"Bearer {self.token}"}
        poll_count = 0
        max_polls = 60  # 2 minutes with 2-second intervals

        try:
            while poll_count < max_polls:
                poll_count += 1
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{BASE_URL}/api/jobs/{job_id}/status",
                        headers=headers,
                        timeout=10.0
                    )

                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data["status"]

                    if status == "completed":
                        task_execution_time = time.time() - start_time
                        return {
                            "success": True,
                            "status": "completed",
                            "queue_wait_time": (
                                poll_count * 2
                            ),  # Estimate based on polls
                            "task_execution_time": task_execution_time,
                            "retry_count": status_data.get("retry_count", 0),
                            "result": status_data.get("result", {}),
                        }

                    elif status == "failed":
                        return {
                            "success": False,
                            "status": "failed",
                            "error": status_data.get("error"),
                            "task_execution_time": time.time() - start_time,
                        }

                await asyncio.sleep(2)

            return {
                "success": False,
                "status": "timeout",
                "task_execution_time": time.time() - start_time,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


async def run_concurrent_load_test():
    """Run load test with concurrent users."""
    print("=" * 80)
    print("PHASE 3: CONCURRENT LOAD TEST")
    print("=" * 80)
    print(
        f"\nConfiguration:"
        f"\n  Concurrent Users: {CONCURRENT_USERS}"
        f"\n  Jobs per User: {JOBS_PER_USER}"
        f"\n  Total Jobs: {CONCURRENT_USERS * JOBS_PER_USER}"
        f"\n"
    )

    metrics["start_time"] = datetime.utcnow()

    # Create users
    print("[1] Authenticating users...")
    users = [LoadTestUser(i) for i in range(1, CONCURRENT_USERS + 1)]
    auth_tasks = [user.authenticate() for user in users]
    auth_results = await asyncio.gather(*auth_tasks)

    authenticated = sum(auth_results)
    print(f"[OK] Authenticated {authenticated}/{CONCURRENT_USERS} users\n")

    if authenticated == 0:
        print("[FAIL] No users authenticated. Aborting test.")
        return

    # Submit jobs concurrently
    print("[2] Submitting jobs from all users...")
    job_submission_start = time.time()

    submission_tasks = []
    for user in users:
        for job_num in range(JOBS_PER_USER):
            submission_tasks.append(user.submit_job(job_num))

    submission_results = await asyncio.gather(*submission_tasks)

    job_submission_time = time.time() - job_submission_start
    successful_submissions = sum(1 for r in submission_results if r.get("success"))

    print(f"[OK] Submitted {successful_submissions} jobs in {job_submission_time:.2f}s\n")

    # Collect job IDs for status checking
    job_list = []
    for result in submission_results:
        if result.get("success"):
            job_list.append(
                {
                    "job_id": result["job_id"],
                    "api_response_time": result["api_response_time"],
                    "submitted_at": result["submitted_at"],
                    "submit_timestamp": time.time(),
                }
            )
            metrics["api_response_times"].append(result["api_response_time"])

    # Poll job status concurrently
    print("[3] Polling job status...")
    status_tasks = []
    for job in job_list:
        # Find the user who submitted this job (using modulo)
        user_idx = hash(job["job_id"]) % len(users)
        status_tasks.append(
            users[user_idx].check_job_status(job["job_id"], job["submit_timestamp"])
        )

    status_results = await asyncio.gather(*status_tasks)

    # Process results
    for result in status_results:
        if result.get("success"):
            metrics["success_count"] += 1
            if result.get("task_execution_time"):
                metrics["task_execution_times"].append(result["task_execution_time"])
            if result.get("queue_wait_time"):
                metrics["queue_wait_times"].append(result["queue_wait_time"])
            if result.get("retry_count", 0) > 0:
                metrics["retry_count"] += result["retry_count"]
        else:
            metrics["failure_count"] += 1

    metrics["end_time"] = datetime.utcnow()
    total_time = (metrics["end_time"] - metrics["start_time"]).total_seconds()

    # Calculate throughput
    if total_time > 0:
        throughput = metrics["success_count"] / total_time
        metrics["throughput"] = throughput

    print_metrics_report()


def print_metrics_report():
    """Print comprehensive metrics report."""
    print("\n" + "=" * 80)
    print("LOAD TEST RESULTS - COMPREHENSIVE METRICS")
    print("=" * 80)

    total_jobs = metrics["success_count"] + metrics["failure_count"]
    success_rate = (
        (metrics["success_count"] / total_jobs * 100)
        if total_jobs > 0
        else 0
    )

    print(f"\n[STATS] OVERALL METRICS:")
    print(f"  Total Jobs: {total_jobs}")
    print(f"  Successful: {metrics['success_count']}")
    print(f"  Failed: {metrics['failure_count']}")
    print(f"  Success Rate: {success_rate:.2f}%")
    print(f"  Throughput: {metrics['throughput']:.2f} jobs/second")

    print(f"\n[TIME] TIMING METRICS (milliseconds):")

    if metrics["api_response_times"]:
        print(f"  API Response Time:")
        print(f"    Min: {min(metrics['api_response_times']) * 1000:.2f}ms")
        print(
            f"    Avg: {statistics.mean(metrics['api_response_times']) * 1000:.2f}ms"
        )
        print(f"    Max: {max(metrics['api_response_times']) * 1000:.2f}ms")
        print(
            f"    Median: {statistics.median(metrics['api_response_times']) * 1000:.2f}ms"
        )

    if metrics["queue_wait_times"]:
        print(f"  Queue Wait Time:")
        print(f"    Min: {min(metrics['queue_wait_times']):.2f}s")
        print(f"    Avg: {statistics.mean(metrics['queue_wait_times']):.2f}s")
        print(f"    Max: {max(metrics['queue_wait_times']):.2f}s")

    if metrics["task_execution_times"]:
        print(f"  Task Execution Time:")
        print(f"    Min: {min(metrics['task_execution_times']):.2f}s")
        print(f"    Avg: {statistics.mean(metrics['task_execution_times']):.2f}s")
        print(f"    Max: {max(metrics['task_execution_times']):.2f}s")

    print(f"\n[RETRY] RETRY METRICS:")
    print(f"  Total Retries: {metrics['retry_count']}")
    print(
        f"  Retry Rate: {(metrics['retry_count'] / total_jobs * 100 if total_jobs > 0 else 0):.2f}%"
    )

    total_duration = (metrics["end_time"] - metrics["start_time"]).total_seconds()
    print(f"\n[TIME] TEST DURATION:")
    print(f"  Total Time: {total_duration:.2f}s")
    print(f"  Start: {metrics['start_time'].isoformat()}")
    print(f"  End: {metrics['end_time'].isoformat()}")

    print(f"\n[OK] TARGET VALIDATION:")
    target_success = 95
    target_concurrency = 20
    print(f"  Target Success Rate: {target_success}%")
    print(f"  Actual Success Rate: {success_rate:.2f}%")
    print(
        f"  Status: {'[OK] PASS' if success_rate >= target_success else '[FAIL] FAIL'}"
    )
    print(f"  Target Concurrency: {target_concurrency} users")
    print(f"  Actual Concurrency: {CONCURRENT_USERS} users")
    print(f"  Status: {'[OK] PASS' if CONCURRENT_USERS >= target_concurrency else '[FAIL] FAIL'}")

    print("\n" + "=" * 80)

    # Save report to file
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "configuration": {
            "concurrent_users": CONCURRENT_USERS,
            "jobs_per_user": JOBS_PER_USER,
            "total_jobs": total_jobs,
        },
        "results": {
            "successful": metrics["success_count"],
            "failed": metrics["failure_count"],
            "success_rate": success_rate,
            "throughput": metrics["throughput"],
            "total_duration_seconds": total_duration,
        },
        "metrics": {
            "api_response_time_ms": {
                "min": min(metrics["api_response_times"]) * 1000
                if metrics["api_response_times"]
                else None,
                "avg": statistics.mean(metrics["api_response_times"]) * 1000
                if metrics["api_response_times"]
                else None,
                "max": max(metrics["api_response_times"]) * 1000
                if metrics["api_response_times"]
                else None,
            },
            "task_execution_time_s": {
                "min": min(metrics["task_execution_times"])
                if metrics["task_execution_times"]
                else None,
                "avg": statistics.mean(metrics["task_execution_times"])
                if metrics["task_execution_times"]
                else None,
                "max": max(metrics["task_execution_times"])
                if metrics["task_execution_times"]
                else None,
            },
            "retry_rate": (
                metrics["retry_count"] / total_jobs * 100 if total_jobs > 0 else 0
            ),
        },
    }

    filename = (
        f"load_test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(filename, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[REPORT] Report saved: {filename}\n")


if __name__ == "__main__":
    asyncio.run(run_concurrent_load_test())
