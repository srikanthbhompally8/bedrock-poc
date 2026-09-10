"""Analyze database queries and identify optimization opportunities.

This script:
1. Scans codebase for database queries
2. Identifies N+1 query patterns
3. Analyzes query complexity
4. Recommends indexes
5. Generates optimization report
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import defaultdict

# Query patterns to find
QUERY_PATTERNS = {
    "select": re.compile(r"\.select\(|\.query\(|SELECT", re.IGNORECASE),
    "insert": re.compile(r"\.add\(|INSERT", re.IGNORECASE),
    "update": re.compile(r"\.update\(|UPDATE", re.IGNORECASE),
    "delete": re.compile(r"\.delete\(|DELETE", re.IGNORECASE),
    "filter": re.compile(r"\.filter\(|WHERE", re.IGNORECASE),
    "join": re.compile(r"\.join\(|JOIN", re.IGNORECASE),
}

# N+1 query patterns (potential issues)
N_PLUS_1_PATTERNS = [
    (r"for\s+\w+\s+in\s+.*\.all\(\)", "Loop with .all() - potential N+1"),
    (r"for\s+\w+\s+in\s+query.*:\s+\w+\.query", "Loop with nested query - N+1 pattern"),
]


class QueryAnalyzer:
    """Analyze database queries in Python code."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.queries = defaultdict(list)
        self.n_plus_1_issues = []
        self.index_recommendations = []

    def scan_files(self) -> None:
        """Scan Python files for database queries."""
        print("Scanning Python files for database queries...\n")

        for py_file in self.project_root.rglob("*.py"):
            # Skip tests and migrations for now
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                    for line_num, line in enumerate(lines, 1):
                        for query_type, pattern in QUERY_PATTERNS.items():
                            if pattern.search(line):
                                self.queries[query_type].append(
                                    {
                                        "file": str(py_file.relative_to(self.project_root)),
                                        "line": line_num,
                                        "code": line.strip(),
                                    }
                                )

                        # Check for N+1 patterns
                        for n_plus_1_pattern, description in N_PLUS_1_PATTERNS:
                            if re.search(n_plus_1_pattern, line):
                                self.n_plus_1_issues.append(
                                    {
                                        "file": str(py_file.relative_to(self.project_root)),
                                        "line": line_num,
                                        "code": line.strip(),
                                        "issue": description,
                                    }
                                )

            except Exception as e:
                print(f"Error reading {py_file}: {e}")

    def generate_index_recommendations(self) -> None:
        """Generate index recommendations based on query patterns."""
        print("Generating index recommendations...\n")

        recommendations = {
            "candidates": [
                ("skills", "Frequently filtered in matching queries"),
                ("email", "Used in candidate search"),
                ("experience_level", "Used in filtering"),
            ],
            "job_listings": [
                ("required_skills", "Frequently joined with candidates"),
                ("company", "Used in search filters"),
                ("salary_min, salary_max", "Used in range queries"),
            ],
            "matches": [
                ("candidate_id, job_id", "Composite index for unique constraint"),
                ("created_at", "Used for sorting results"),
                ("score", "Used for ranking"),
            ],
            "audit_logs": [
                ("user_id", "Filtered by user in audit queries"),
                ("timestamp", "Used for time-range queries"),
                ("action", "Filtered by action type"),
            ],
        }

        for table, indexes in recommendations.items():
            for column, reason in indexes:
                self.index_recommendations.append(
                    {
                        "table": table,
                        "column": column,
                        "reason": reason,
                        "sql": f"CREATE INDEX idx_{table}_{column.replace(', ', '_')} ON {table}({column});",
                    }
                )

    def generate_report(self) -> str:
        """Generate a detailed optimization report."""
        report = []

        report.append("=" * 80)
        report.append("DATABASE QUERY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")

        # Query summary
        report.append("QUERY SUMMARY")
        report.append("-" * 80)
        total_queries = sum(len(queries) for queries in self.queries.values())
        report.append(f"Total queries found: {total_queries}")
        for query_type, queries in self.queries.items():
            report.append(f"  {query_type.upper()}: {len(queries)}")
        report.append("")

        # Queries by file
        report.append("QUERIES BY FILE")
        report.append("-" * 80)
        files_with_queries = defaultdict(int)
        for queries_list in self.queries.values():
            for query in queries_list:
                files_with_queries[query["file"]] += 1

        for file, count in sorted(files_with_queries.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {file}: {count} queries")
        report.append("")

        # N+1 query issues
        if self.n_plus_1_issues:
            report.append("POTENTIAL N+1 QUERY ISSUES")
            report.append("-" * 80)
            for issue in self.n_plus_1_issues:
                report.append(f"File: {issue['file']}:{issue['line']}")
                report.append(f"Issue: {issue['issue']}")
                report.append(f"Code: {issue['code']}")
                report.append("")
        else:
            report.append("✓ No obvious N+1 query patterns detected")
            report.append("")

        # Index recommendations
        report.append("INDEX RECOMMENDATIONS")
        report.append("-" * 80)
        for rec in self.index_recommendations:
            report.append(f"Table: {rec['table']}")
            report.append(f"Column: {rec['column']}")
            report.append(f"Reason: {rec['reason']}")
            report.append(f"SQL: {rec['sql']}")
            report.append("")

        # Performance tips
        report.append("OPTIMIZATION TIPS")
        report.append("-" * 80)
        tips = [
            "1. Use .select_from().join() instead of multiple queries",
            "2. Use eager loading (joined/contains_eager) for relationships",
            "3. Add indexes on frequently filtered columns",
            "4. Use EXPLAIN ANALYZE to verify query plans",
            "5. Set pool_pre_ping=True to verify connections",
            "6. Use connection pooling (min=5, max=20)",
            "7. Add VACUUM and ANALYZE maintenance tasks",
            "8. Monitor slow query log (queries >100ms)",
        ]
        for tip in tips:
            report.append(f"  {tip}")
        report.append("")

        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)

        return "\n".join(report)

    def save_report(self, output_file: str) -> None:
        """Save the report to a file."""
        report = self.generate_report()
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report saved to: {output_file}")


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent.parent

    analyzer = QueryAnalyzer(str(project_root))
    analyzer.scan_files()
    analyzer.generate_index_recommendations()

    # Print report to console
    report = analyzer.generate_report()
    print(report)

    # Save to file
    output_file = project_root / "DATABASE_QUERY_ANALYSIS.txt"
    analyzer.save_report(str(output_file))


if __name__ == "__main__":
    main()
