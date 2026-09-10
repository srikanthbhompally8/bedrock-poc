#!/usr/bin/env python3
"""
Complete Performance Testing Suite - Task 4.5
Captures comprehensive metrics including response times, throughput, resource utilization,
and system behavior under various load conditions.
"""

import asyncio
import json
import logging
import time
import psutil
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent
REPORTS_DIR = PROJECT_ROOT / "performance_reports"
REPORTS_DIR.mkdir(exist_ok=True)


class SystemMetricsCollector:
    """Collects CPU, memory, and other system metrics during tests."""

    def __init__(self):
        self.metrics = {
            "cpu": [],
            "memory": [],
            "disk": [],
            "connections": []
        }

    def collect(self):
        """Collect current system metrics."""
        try:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            self.metrics["cpu"].append({
                "timestamp": datetime.now().isoformat(),
                "percent": cpu
            })

            self.metrics["memory"].append({
                "timestamp": datetime.now().isoformat(),
                "percent": memory.percent,
                "used_mb": memory.used / (1024 * 1024),
                "available_mb": memory.available / (1024 * 1024)
            })

            self.metrics["disk"].append({
                "timestamp": datetime.now().isoformat(),
                "percent": disk.percent,
                "free_mb": disk.free / (1024 * 1024)
            })
        except Exception as e:
            log.error(f"Error collecting metrics: {e}")

    def get_summary(self):
        """Get summary statistics of collected metrics."""
        summary = {}

        if self.metrics["cpu"]:
            cpu_values = [m["percent"] for m in self.metrics["cpu"]]
            summary["cpu"] = {
                "min": min(cpu_values),
                "max": max(cpu_values),
                "avg": sum(cpu_values) / len(cpu_values)
            }

        if self.metrics["memory"]:
            mem_values = [m["percent"] for m in self.metrics["memory"]]
            mem_used = [m["used_mb"] for m in self.metrics["memory"]]
            summary["memory"] = {
                "min_percent": min(mem_values),
                "max_percent": max(mem_values),
                "avg_percent": sum(mem_values) / len(mem_values),
                "peak_used_mb": max(mem_used)
            }

        if self.metrics["disk"]:
            disk_values = [m["percent"] for m in self.metrics["disk"]]
            summary["disk"] = {
                "min_percent": min(disk_values),
                "max_percent": max(disk_values),
                "avg_percent": sum(disk_values) / len(disk_values)
            }

        return summary


class PerformanceTestExecutor:
    """Executes complete performance testing suite."""

    def __init__(self):
        self.metrics_collector = SystemMetricsCollector()
        self.test_results = {}
        self.start_time = None

    def run_baseline_test(self):
        """Run baseline performance test (10 users, 5 minutes)."""
        log.info("="*80)
        log.info("BASELINE PERFORMANCE TEST (10 Concurrent Users)")
        log.info("="*80)

        try:
            from tests.test_load_performance import LoadTestScenarios, format_results_table

            self.start_time = time.time()

            # Start metrics collection in background
            metrics_task = asyncio.create_task(self._collect_metrics_background(60))

            # Run baseline test
            baseline_results = asyncio.run(LoadTestScenarios.baseline_performance_test())
            print(format_results_table(baseline_results))

            self.test_results["baseline"] = baseline_results

            # Wait for metrics
            asyncio.run(metrics_task)

            return True
        except Exception as e:
            log.error(f"Baseline test failed: {e}")
            return False

    def run_load_test(self):
        """Run load performance test (100 users, 1 minute)."""
        log.info("="*80)
        log.info("LOAD PERFORMANCE TEST (100 Concurrent Users)")
        log.info("="*80)

        try:
            from tests.test_load_performance import LoadTestScenarios, format_results_table

            # Run load test
            load_results = asyncio.run(LoadTestScenarios.load_test())
            print(format_results_table(load_results))

            self.test_results["load"] = load_results
            return True
        except Exception as e:
            log.error(f"Load test failed: {e}")
            return False

    def run_stress_test(self):
        """Run stress test (gradual increase to 50+ users)."""
        log.info("="*80)
        log.info("STRESS TEST (Gradual Load Increase)")
        log.info("="*80)

        try:
            from tests.test_load_performance import LoadTestScenarios, format_results_table

            # Run stress test
            stress_results = asyncio.run(LoadTestScenarios.stress_test())
            print(format_results_table(stress_results))

            self.test_results["stress"] = stress_results
            return True
        except Exception as e:
            log.error(f"Stress test failed: {e}")
            return False

    async def _collect_metrics_background(self, duration):
        """Collect system metrics in background for specified duration."""
        end_time = time.time() + duration
        while time.time() < end_time:
            self.metrics_collector.collect()
            await asyncio.sleep(5)

    def generate_report(self):
        """Generate comprehensive performance report."""
        log.info("="*80)
        log.info("GENERATING COMPREHENSIVE PERFORMANCE REPORT")
        log.info("="*80)

        report = {
            "timestamp": datetime.now().isoformat(),
            "test_results": {},
            "system_metrics": self.metrics_collector.get_summary(),
            "summary": self._generate_summary()
        }

        # Convert test results to JSON-serializable format
        for test_name, results in self.test_results.items():
            if hasattr(results, '__dict__'):
                report["test_results"][test_name] = self._serialize_results(results)
            else:
                report["test_results"][test_name] = results

        # Save report
        report_file = REPORTS_DIR / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        log.info(f"Report saved to: {report_file}")

        # Print summary
        print("\n" + "="*80)
        print("PERFORMANCE TEST SUMMARY")
        print("="*80)
        print(json.dumps(report, indent=2, default=str))

        return report

    def _serialize_results(self, results):
        """Convert results object to JSON-serializable dict."""
        result_dict = {}
        for key, value in results.__dict__.items():
            if isinstance(value, list):
                result_dict[key] = [str(v) if not isinstance(v, (int, float, str, bool)) else v for v in value]
            elif isinstance(value, (int, float, str, bool)):
                result_dict[key] = value
            else:
                result_dict[key] = str(value)
        return result_dict

    def _generate_summary(self):
        """Generate test summary with key findings."""
        summary = {
            "tests_executed": len(self.test_results),
            "tests_passed": len(self.test_results),
            "key_findings": [],
            "bottlenecks": [],
            "recommendations": []
        }

        # Analyze results
        if "baseline" in self.test_results:
            baseline = self.test_results["baseline"]
            summary["key_findings"].append(
                f"Baseline: Avg response time {baseline.avg_response_time_ms:.2f}ms, "
                f"Error rate {baseline.error_rate:.2f}%"
            )

            if baseline.error_rate > 1:
                summary["bottlenecks"].append("High error rate at baseline load")
                summary["recommendations"].append("Investigate error causes before peak load testing")

        if "load" in self.test_results:
            load = self.test_results["load"]
            summary["key_findings"].append(
                f"Load test: Avg response time {load.avg_response_time_ms:.2f}ms, "
                f"Error rate {load.error_rate:.2f}%"
            )

        # System metrics analysis
        metrics = self.metrics_collector.get_summary()
        if metrics.get("cpu", {}).get("max", 0) > 80:
            summary["bottlenecks"].append("CPU usage exceeded 80%")
            summary["recommendations"].append("Consider CPU optimization or scaling")

        if metrics.get("memory", {}).get("max_percent", 0) > 75:
            summary["bottlenecks"].append("Memory usage exceeded 75%")
            summary["recommendations"].append("Profile and optimize memory allocation")

        return summary

    def run_all_tests(self):
        """Execute complete testing suite."""
        print("\n" + "*"*80)
        print("*" + " BEDROCK POC - COMPLETE PERFORMANCE TESTING SUITE ".center(78) + "*")
        print("*"*80 + "\n")

        # Prerequisites check
        log.info("Checking prerequisites...")
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'postgres'),
                database=os.getenv('DB_NAME', 'bedrock_poc')
            )
            conn.close()
            log.info("Database: OK")
        except Exception as e:
            log.error(f"Database check failed: {e}")
            return False

        import httpx
        try:
            with httpx.Client() as client:
                response = client.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    log.info("API server: OK")
                else:
                    log.error("API server not ready")
                    return False
        except Exception as e:
            log.error(f"API server check failed: {e}")
            return False

        # Run tests
        success = True
        success = self.run_baseline_test() and success
        success = self.run_load_test() and success
        success = self.run_stress_test() and success

        # Generate report
        if success:
            self.generate_report()
            print("\n" + "*"*80)
            print("*" + " TESTING COMPLETE ".center(78) + "*")
            print("*"*80)
            return True
        else:
            log.error("Testing failed")
            return False


def main():
    """Main entry point."""
    executor = PerformanceTestExecutor()
    success = executor.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
