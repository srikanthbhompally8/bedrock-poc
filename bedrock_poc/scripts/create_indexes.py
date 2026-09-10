"""Create performance indexes for production database.

This script creates indexes on frequently filtered and joined columns
to improve query performance.
"""

import logging
from bedrock_poc.config.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Performance indexes to create
PERFORMANCE_INDEXES = [
    # Candidates table - frequently filtered in matching
    {
        "name": "idx_candidates_skills",
        "table": "candidates",
        "column": "skills",
        "reason": "Frequently filtered in matching queries",
    },
    {
        "name": "idx_candidates_email",
        "table": "candidates",
        "column": "email",
        "reason": "Used in candidate search",
    },
    {
        "name": "idx_candidates_experience",
        "table": "candidates",
        "column": "experience_level",
        "reason": "Used in filtering and matching",
    },
    # Job listings table - frequently joined with candidates
    {
        "name": "idx_job_listings_required_skills",
        "table": "job_listings",
        "column": "required_skills",
        "reason": "Frequently joined with candidates",
    },
    {
        "name": "idx_job_listings_company",
        "table": "job_listings",
        "column": "company",
        "reason": "Used in search filters",
    },
    # Matches table - frequently filtered and sorted
    {
        "name": "idx_matches_candidate_job",
        "table": "matches",
        "columns": "candidate_id, job_id",
        "reason": "Composite index for lookups",
        "unique": False,
    },
    {
        "name": "idx_matches_created_at",
        "table": "matches",
        "column": "created_at",
        "reason": "Used for sorting results",
    },
    {
        "name": "idx_matches_score",
        "table": "matches",
        "column": "score",
        "reason": "Used for ranking",
    },
    # Audit logs table - frequently filtered
    {
        "name": "idx_audit_logs_user_id",
        "table": "audit_logs",
        "column": "user_id",
        "reason": "Filtered by user in audit queries",
    },
    {
        "name": "idx_audit_logs_timestamp",
        "table": "audit_logs",
        "column": "timestamp",
        "reason": "Used for time-range queries",
    },
    {
        "name": "idx_audit_logs_action",
        "table": "audit_logs",
        "column": "action",
        "reason": "Filtered by action type",
    },
]


def create_indexes():
    """Create all performance indexes."""
    engine = DatabaseManager.get_engine()

    logger.info("Creating performance indexes...")
    logger.info("=" * 80)

    created_count = 0
    skipped_count = 0
    error_count = 0

    with engine.connect() as conn:
        for index_config in PERFORMANCE_INDEXES:
            try:
                index_name = index_config["name"]
                table = index_config["table"]
                columns = index_config.get("columns") or index_config.get("column")
                reason = index_config["reason"]

                # Check if index already exists
                result = conn.execute(
                    f"""
                    SELECT 1 FROM pg_indexes
                    WHERE indexname = '{index_name}'
                    """
                )

                if result.fetchone():
                    logger.warning(f"✓ Index {index_name} already exists (skipping)")
                    skipped_count += 1
                    continue

                # Create index
                create_sql = f"CREATE INDEX {index_name} ON {table}({columns})"
                conn.execute(create_sql)
                conn.commit()

                logger.info(f"✓ Created index {index_name}")
                logger.info(f"  Table: {table}")
                logger.info(f"  Columns: {columns}")
                logger.info(f"  Reason: {reason}")
                logger.info("")

                created_count += 1

            except Exception as e:
                logger.error(f"✗ Failed to create index {index_config['name']}: {e}")
                error_count += 1

    logger.info("=" * 80)
    logger.info(f"Index creation summary:")
    logger.info(f"  Created: {created_count}")
    logger.info(f"  Skipped: {skipped_count}")
    logger.info(f"  Errors: {error_count}")
    logger.info("")

    if error_count == 0:
        logger.info("✓ All indexes created successfully!")
    else:
        logger.warning(f"⚠ {error_count} indexes failed to create")


def analyze_indexes():
    """Analyze and display index statistics."""
    engine = DatabaseManager.get_engine()

    logger.info("Index Statistics:")
    logger.info("=" * 80)

    with engine.connect() as conn:
        result = conn.execute(
            """
            SELECT
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY tablename, indexname
            """
        )

        for row in result:
            logger.info(f"Table: {row[1]}")
            logger.info(f"Index: {row[2]}")
            logger.info(f"Definition: {row[3]}")
            logger.info("")


def main():
    """Main entry point."""
    logger.info("Database Performance Index Creation Tool")
    logger.info("=" * 80)
    logger.info("")

    # Create indexes
    create_indexes()

    logger.info("")

    # Show index statistics
    analyze_indexes()

    logger.info("Index creation complete!")


if __name__ == "__main__":
    main()
