"""Benchmark database performance before and after optimizations.

Measures query execution time for critical database operations.
"""

import time
import logging
from sqlalchemy import func
from bedrock_poc.config.database import DatabaseManager
from bedrock_poc.models_db import Candidate, JobListing, Match, AuditLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseBenchmark:
    """Benchmark database query performance."""

    def __init__(self):
        self.session = DatabaseManager.get_session()
        self.results = []

    def benchmark_query(self, name: str, query_func) -> float:
        """Benchmark a single query.

        Args:
            name: Query name/description
            query_func: Function that executes the query

        Returns:
            Execution time in milliseconds
        """
        try:
            start_time = time.time()
            query_func()
            duration_ms = (time.time() - start_time) * 1000

            status = "✓" if duration_ms < 100 else "⚠"
            logger.info(f"{status} {name}: {duration_ms:.2f}ms")

            self.results.append({"name": name, "duration_ms": duration_ms, "status": status})

            return duration_ms

        except Exception as e:
            logger.error(f"✗ {name}: {e}")
            self.results.append({"name": name, "error": str(e)})
            return None

    def run_benchmarks(self) -> None:
        """Run all performance benchmarks."""
        logger.info("Database Performance Benchmarks")
        logger.info("=" * 80)
        logger.info("")

        # Candidate queries
        logger.info("CANDIDATE QUERIES")
        logger.info("-" * 80)

        self.benchmark_query(
            "Get all candidates", lambda: self.session.query(Candidate).all()
        )

        self.benchmark_query(
            "Find candidates by experience level",
            lambda: self.session.query(Candidate)
            .filter(Candidate.experience_level == "intermediate")
            .all(),
        )

        self.benchmark_query(
            "Count candidates", lambda: self.session.query(func.count(Candidate.id)).scalar()
        )

        # Job listing queries
        logger.info("")
        logger.info("JOB LISTING QUERIES")
        logger.info("-" * 80)

        self.benchmark_query(
            "Get all job listings", lambda: self.session.query(JobListing).all()
        )

        self.benchmark_query(
            "Find jobs by company",
            lambda: self.session.query(JobListing)
            .filter(JobListing.company == "TechCorp")
            .all(),
        )

        # Match queries
        logger.info("")
        logger.info("MATCH QUERIES")
        logger.info("-" * 80)

        self.benchmark_query("Get all matches", lambda: self.session.query(Match).all())

        self.benchmark_query(
            "Find matches by candidate",
            lambda: self.session.query(Match).filter(Match.candidate_id == 1).all(),
        )

        self.benchmark_query(
            "Get matches by date",
            lambda: self.session.query(Match)
            .order_by(Match.created_at.desc())
            .limit(100)
            .all(),
        )

        self.benchmark_query(
            "Get top matches by score",
            lambda: self.session.query(Match)
            .order_by(Match.score.desc())
            .limit(10)
            .all(),
        )

        # Audit log queries
        logger.info("")
        logger.info("AUDIT LOG QUERIES")
        logger.info("-" * 80)

        self.benchmark_query(
            "Get recent audit logs",
            lambda: self.session.query(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .limit(100)
            .all(),
        )

        self.benchmark_query(
            "Get audit logs by user",
            lambda: self.session.query(AuditLog).filter(AuditLog.user_id == "user1").all(),
        )

        # Summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("BENCHMARK SUMMARY")
        logger.info("-" * 80)

        total_queries = len(self.results)
        successful_queries = sum(1 for r in self.results if "duration_ms" in r)
        slow_queries = sum(1 for r in self.results if r.get("duration_ms", 0) >= 100)

        logger.info(f"Total queries: {total_queries}")
        logger.info(f"Successful: {successful_queries}")
        logger.info(f"Slow (>100ms): {slow_queries}")

        if slow_queries > 0:
            logger.warning("")
            logger.warning("Slow queries (>100ms):")
            for result in self.results:
                if result.get("duration_ms", 0) >= 100:
                    logger.warning(f"  - {result['name']}: {result['duration_ms']:.2f}ms")

        logger.info("")
        logger.info("Average query time: {:.2f}ms".format(
            sum(r.get("duration_ms", 0) for r in self.results if "duration_ms" in r)
            / successful_queries
            if successful_queries > 0
            else 0
        ))

        logger.info("=" * 80)

    def close(self) -> None:
        """Close database session."""
        self.session.close()


def main():
    """Main entry point."""
    logger.info("Database Performance Benchmarking Tool")
    logger.info("")

    benchmark = DatabaseBenchmark()
    try:
        benchmark.run_benchmarks()
    finally:
        benchmark.close()

    logger.info("Benchmark complete!")


if __name__ == "__main__":
    main()
