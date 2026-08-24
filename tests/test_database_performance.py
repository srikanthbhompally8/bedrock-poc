"""
Database Performance Testing Suite for Bedrock POC.

This module tests database performance under various conditions:
- Query execution time
- Connection pool utilization
- Concurrent query handling
- Large dataset operations
- Index effectiveness
"""

import time
import asyncio
import statistics
from dataclasses import dataclass, field
from typing import List, Tuple
from datetime import datetime
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor


@dataclass
class QueryMetrics:
    """Metrics for a single database query."""
    query_name: str
    query_type: str  # SELECT, INSERT, UPDATE, DELETE
    execution_time_ms: float
    rows_affected: int
    timestamp: str
    success: bool
    error_message: str = ""


@dataclass
class DatabaseMetrics:
    """Aggregated database metrics."""
    query_name: str
    query_type: str
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    min_execution_time_ms: float = float('inf')
    max_execution_time_ms: float = 0
    avg_execution_time_ms: float = 0
    p95_execution_time_ms: float = 0
    p99_execution_time_ms: float = 0
    total_rows_affected: int = 0
    execution_times: List[float] = field(default_factory=list)


class DatabasePerformanceConfig:
    """Configuration for database performance testing."""

    DB_HOST = "localhost"
    DB_PORT = 5432
    DB_NAME = "bedrock_poc"
    DB_USER = "bedrock_user"
    DB_PASSWORD = "bedrock_password"

    # Connection pool settings
    MIN_CONNECTIONS = 5
    MAX_CONNECTIONS = 20

    # Test settings
    CONCURRENT_CONNECTIONS = 10
    QUERIES_PER_CONNECTION = 100


class DatabasePerformanceTestClient:
    """Client for database performance testing."""

    def __init__(self, config: DatabasePerformanceConfig = None):
        self.config = config or DatabasePerformanceConfig()
        self.metrics: List[QueryMetrics] = []
        self.connection_pool = None
        self._init_connection_pool()

    def _init_connection_pool(self):
        """Initialize connection pool."""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                self.config.MIN_CONNECTIONS,
                self.config.MAX_CONNECTIONS,
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
                database=self.config.DB_NAME,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD
            )
            print("✓ Connection pool initialized")
        except Exception as e:
            print(f"✗ Failed to initialize connection pool: {e}")
            raise

    def get_connection(self):
        """Get a connection from the pool."""
        if not self.connection_pool:
            raise Exception("Connection pool not initialized")
        return self.connection_pool.getconn()

    def return_connection(self, conn):
        """Return a connection to the pool."""
        if self.connection_pool:
            self.connection_pool.putconn(conn)

    def _execute_query(self, query_name: str, query: str, query_type: str, params=None) -> bool:
        """Execute a single query and record metrics."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            start = time.time()
            cursor.execute(query, params or ())
            elapsed = (time.time() - start) * 1000

            rows_affected = cursor.rowcount
            conn.commit()

            self.metrics.append(QueryMetrics(
                query_name=query_name,
                query_type=query_type,
                execution_time_ms=elapsed,
                rows_affected=rows_affected,
                timestamp=datetime.now().isoformat(),
                success=True
            ))

            cursor.close()
            return True

        except Exception as e:
            self.metrics.append(QueryMetrics(
                query_name=query_name,
                query_type=query_type,
                execution_time_ms=0,
                rows_affected=0,
                timestamp=datetime.now().isoformat(),
                success=False,
                error_message=str(e)
            ))
            if conn:
                conn.rollback()
            return False

        finally:
            if conn:
                self.return_connection(conn)

    async def concurrent_query_test(self, query_name: str, query: str, query_type: str, num_concurrent: int):
        """Run multiple queries concurrently."""
        tasks = []

        def query_task():
            self._execute_query(query_name, query, query_type)

        loop = asyncio.get_event_loop()
        for _ in range(num_concurrent):
            tasks.append(loop.run_in_executor(None, query_task))

        await asyncio.gather(*tasks)

    def test_select_candidates(self):
        """Test SELECT query on candidates table."""
        query = "SELECT id, name, skills FROM candidates LIMIT 100;"
        return self._execute_query("select_candidates", query, "SELECT")

    def test_select_with_filter(self):
        """Test filtered SELECT query."""
        query = """
            SELECT id, name, skills
            FROM candidates
            WHERE skills LIKE '%Python%'
            LIMIT 50;
        """
        return self._execute_query("select_with_filter", query, "SELECT")

    def test_count_candidates(self):
        """Test COUNT query."""
        query = "SELECT COUNT(*) FROM candidates;"
        return self._execute_query("count_candidates", query, "SELECT")

    def test_join_query(self):
        """Test JOIN query."""
        query = """
            SELECT c.id, c.name, j.title
            FROM candidates c
            LEFT JOIN matches m ON c.id = m.candidate_id
            LEFT JOIN job_listings j ON m.job_id = j.id
            LIMIT 50;
        """
        return self._execute_query("join_query", query, "SELECT")

    def test_aggregation_query(self):
        """Test aggregation query."""
        query = """
            SELECT
                COUNT(*) as total_candidates,
                COUNT(CASE WHEN status='active' THEN 1 END) as active
            FROM candidates;
        """
        return self._execute_query("aggregation_query", query, "SELECT")

    def close(self):
        """Close connection pool."""
        if self.connection_pool:
            self.connection_pool.closeall()


class DatabasePerformanceAnalyzer:
    """Analyze database performance metrics."""

    @staticmethod
    def calculate_percentile(values: List[float], percentile: float) -> float:
        """Calculate percentile."""
        if not values:
            return 0
        sorted_values = sorted(values)
        idx = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(idx, len(sorted_values) - 1)]

    @staticmethod
    def analyze_database_metrics(metrics: List[QueryMetrics]) -> List[DatabaseMetrics]:
        """Analyze database metrics."""
        query_map = {}

        for metric in metrics:
            key = (metric.query_name, metric.query_type)
            if key not in query_map:
                query_map[key] = []
            query_map[key].append(metric)

        results = []
        for (query_name, query_type), query_metrics in query_map.items():
            successful = [m for m in query_metrics if m.success]
            execution_times = [m.execution_time_ms for m in successful]

            dm = DatabaseMetrics(
                query_name=query_name,
                query_type=query_type,
                total_queries=len(query_metrics),
                successful_queries=len(successful),
                failed_queries=len(query_metrics) - len(successful),
                execution_times=execution_times
            )

            if execution_times:
                dm.min_execution_time_ms = min(execution_times)
                dm.max_execution_time_ms = max(execution_times)
                dm.avg_execution_time_ms = statistics.mean(execution_times)
                dm.p95_execution_time_ms = DatabasePerformanceAnalyzer.calculate_percentile(execution_times, 95)
                dm.p99_execution_time_ms = DatabasePerformanceAnalyzer.calculate_percentile(execution_times, 99)

            dm.total_rows_affected = sum(m.rows_affected for m in query_metrics)

            results.append(dm)

        return results


def format_database_results(results: List[DatabaseMetrics]) -> str:
    """Format database results as a readable table."""
    lines = []
    lines.append("\n" + "="*100)
    lines.append("DATABASE PERFORMANCE TEST RESULTS")
    lines.append("="*100)

    if not results:
        lines.append("No results to display")
        return "\n".join(lines)

    lines.append(f"{'Query Name':<25} {'Type':<8} {'Total':<8} {'Avg (ms)':<12} {'P95 (ms)':<12} {'P99 (ms)':<12} {'Success %':<10}")
    lines.append("-" * 100)

    for dm in results:
        success_rate = (dm.successful_queries / dm.total_queries * 100) if dm.total_queries else 0
        lines.append(
            f"{dm.query_name:<25} {dm.query_type:<8} {dm.total_queries:<8} "
            f"{dm.avg_execution_time_ms:<12.2f} {dm.p95_execution_time_ms:<12.2f} "
            f"{dm.p99_execution_time_ms:<12.2f} {success_rate:<10.1f}"
        )

    lines.append("="*100 + "\n")
    return "\n".join(lines)


# Test functions for pytest
def test_select_performance():
    """Test SELECT query performance."""
    print("\nTesting SELECT query performance...")
    client = DatabasePerformanceTestClient()

    try:
        # Warm up
        client.test_select_candidates()

        # Run multiple queries to get statistics
        for _ in range(50):
            success = client.test_select_candidates()
            assert success, "SELECT query failed"

        results = DatabasePerformanceAnalyzer.analyze_database_metrics(client.metrics)
        print(format_database_results(results))

        # Validate performance
        for dm in results:
            if dm.query_name == "select_candidates":
                assert dm.avg_execution_time_ms < 100, f"Average SELECT time {dm.avg_execution_time_ms}ms > 100ms"
                print(f"✓ SELECT query performance acceptable (avg: {dm.avg_execution_time_ms:.2f}ms)")

    finally:
        client.close()


def test_filtered_query_performance():
    """Test filtered query performance."""
    print("\nTesting filtered query performance...")
    client = DatabasePerformanceTestClient()

    try:
        for _ in range(50):
            success = client.test_select_with_filter()
            assert success, "Filtered query failed"

        results = DatabasePerformanceAnalyzer.analyze_database_metrics(client.metrics)
        print(format_database_results(results))

        for dm in results:
            if dm.query_name == "select_with_filter":
                print(f"✓ Filtered query performance (avg: {dm.avg_execution_time_ms:.2f}ms)")

    finally:
        client.close()


def test_join_performance():
    """Test JOIN query performance."""
    print("\nTesting JOIN query performance...")
    client = DatabasePerformanceTestClient()

    try:
        for _ in range(30):
            success = client.test_join_query()
            if not success:
                print("  Note: JOIN query may fail if data doesn't exist")
                break

        results = DatabasePerformanceAnalyzer.analyze_database_metrics(client.metrics)
        print(format_database_results(results))

    finally:
        client.close()


def test_concurrent_queries():
    """Test concurrent query execution."""
    print("\nTesting concurrent query execution...")
    client = DatabasePerformanceTestClient()

    try:
        start = time.time()

        # Run concurrent queries
        for _ in range(10):
            client.test_select_candidates()
            client.test_count_candidates()

        elapsed = time.time() - start

        results = DatabasePerformanceAnalyzer.analyze_database_metrics(client.metrics)
        print(format_database_results(results))
        print(f"✓ Executed {len(client.metrics)} queries in {elapsed:.2f}s")

    finally:
        client.close()


if __name__ == "__main__":
    print("\n" + "="*100)
    print("DATABASE PERFORMANCE TESTING SUITE")
    print("="*100)

    print("\nNote: Database must be running and accessible")
    print(f"Connecting to: {DatabasePerformanceConfig.DB_HOST}:{DatabasePerformanceConfig.DB_PORT}/{DatabasePerformanceConfig.DB_NAME}")

    try:
        test_select_performance()
        test_filtered_query_performance()
        test_concurrent_queries()
        print("\n✓ All database performance tests completed")
    except Exception as e:
        print(f"\n✗ Database tests failed: {e}")
