#!/usr/bin/env python3
"""
Database Setup and Test Data Population for Performance Testing.

This script:
1. Creates all necessary database tables
2. Populates with test data for performance testing
3. Ensures the database is ready for load tests
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)


def setup_database():
    """Set up the database schema and test data."""
    log.info("Starting database setup...")

    try:
        # Import database components
        from bedrock_poc.database import create_db_engine, get_database_url
        from bedrock_poc.models_db import Base
        from sqlalchemy.orm import sessionmaker

        # Create engine with environment variables
        db_url = get_database_url()
        log.info(f"Connecting to database: {db_url.split('@')[1]}")

        engine = create_db_engine()

        # Create all tables
        log.info("Creating database schema...")
        Base.metadata.create_all(engine)
        log.info("Database schema created successfully")

        # Create session factory and populate test data
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Check if test data already exists
            from bedrock_poc.models_db import JobListing, Resume
            job_count = session.query(JobListing).count()
            resume_count = session.query(Resume).count()

            if job_count == 0:
                log.info("Populating test data...")
                populate_test_data(session)
                log.info(f"Test data created: {session.query(JobListing).count()} jobs, "
                        f"{session.query(Resume).count()} resumes")
            else:
                log.info(f"Test data already exists: {job_count} jobs, {resume_count} resumes")

        finally:
            session.close()

        log.info("Database setup completed successfully!")
        return True

    except Exception as e:
        log.error(f"Database setup failed: {e}", exc_info=True)
        return False


def populate_test_data(session):
    """Populate database with test data for performance testing."""
    from bedrock_poc.models_db import JobListing, Resume
    import json

    try:
        # Sample job descriptions
        sample_jobs = [
            {
                "job_title": "Senior Python Engineer",
                "company": "TechCorp",
                "raw_description": """Senior Software Engineer - Python

                We are looking for a Senior Software Engineer with expertise in Python, FastAPI, and AWS.

                Requirements:
                - 5+ years of Python development
                - FastAPI experience
                - PostgreSQL expertise
                - AWS (EC2, RDS, S3)
                - Docker and Kubernetes
                - Strong communication skills
                """,
                "parsed_data": {
                    "title": "Senior Python Engineer",
                    "company": "TechCorp",
                    "requirements": ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"],
                    "years_required": 5
                }
            },
            {
                "job_title": "Full Stack Developer",
                "company": "WebSystems Inc",
                "raw_description": """Full Stack Developer - React & Python

                Join our team to build modern web applications.

                Requirements:
                - 3+ years of web development
                - React.js
                - Python or Node.js
                - PostgreSQL
                - REST API design
                """,
                "parsed_data": {
                    "title": "Full Stack Developer",
                    "company": "WebSystems Inc",
                    "requirements": ["React", "Python", "PostgreSQL", "REST APIs"],
                    "years_required": 3
                }
            },
            {
                "job_title": "DevOps Engineer",
                "company": "CloudInfra Ltd",
                "raw_description": """DevOps Engineer - Cloud Infrastructure

                Help us build and maintain our cloud infrastructure.

                Requirements:
                - 4+ years of DevOps experience
                - Kubernetes
                - Docker
                - AWS or GCP
                - CI/CD pipelines
                - Infrastructure as Code
                """,
                "parsed_data": {
                    "title": "DevOps Engineer",
                    "company": "CloudInfra Ltd",
                    "requirements": ["Kubernetes", "Docker", "AWS", "CI/CD"],
                    "years_required": 4
                }
            },
            {
                "job_title": "Data Engineer",
                "company": "DataFlow Systems",
                "raw_description": """Data Engineer - Analytics & ETL

                Build data pipelines for analytics.

                Requirements:
                - 3+ years of data engineering
                - Python
                - SQL
                - ETL tools
                - Data warehousing
                """,
                "parsed_data": {
                    "title": "Data Engineer",
                    "company": "DataFlow Systems",
                    "requirements": ["Python", "SQL", "ETL", "Data Warehousing"],
                    "years_required": 3
                }
            },
            {
                "job_title": "Machine Learning Engineer",
                "company": "AI Innovations",
                "raw_description": """ML Engineer - AI/ML Platform

                Work on our AI-powered recruitment platform.

                Requirements:
                - 3+ years of ML engineering
                - Python
                - TensorFlow or PyTorch
                - Model deployment
                - AWS SageMaker
                """,
                "parsed_data": {
                    "title": "Machine Learning Engineer",
                    "company": "AI Innovations",
                    "requirements": ["Python", "TensorFlow", "PyTorch", "AWS"],
                    "years_required": 3
                }
            },
        ]

        # Sample resumes
        sample_resumes = [
            {
                "filename": "alice_johnson.pdf",
                "full_name": "Alice Johnson",
                "email": "alice@example.com",
                "phone": "555-0101",
                "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
                "raw_text": "Alice Johnson with 5 years of backend engineering and AWS expertise",
                "parsed_data": {
                    "name": "Alice Johnson",
                    "email": "alice@example.com",
                    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
                    "experience": "5 years backend engineering, AWS expert"
                }
            },
            {
                "filename": "bob_smith.pdf",
                "full_name": "Bob Smith",
                "email": "bob@example.com",
                "phone": "555-0102",
                "skills": ["React", "Python", "PostgreSQL", "REST APIs"],
                "raw_text": "Bob Smith with 4 years of full stack development experience",
                "parsed_data": {
                    "name": "Bob Smith",
                    "email": "bob@example.com",
                    "skills": ["React", "Python", "PostgreSQL", "REST APIs"],
                    "experience": "4 years full stack development"
                }
            },
            {
                "filename": "carol_williams.pdf",
                "full_name": "Carol Williams",
                "email": "carol@example.com",
                "phone": "555-0103",
                "skills": ["Kubernetes", "Docker", "AWS", "CI/CD"],
                "raw_text": "Carol Williams with 6 years of DevOps and infrastructure experience",
                "parsed_data": {
                    "name": "Carol Williams",
                    "email": "carol@example.com",
                    "skills": ["Kubernetes", "Docker", "AWS", "CI/CD"],
                    "experience": "6 years DevOps and infrastructure"
                }
            },
            {
                "filename": "david_brown.pdf",
                "full_name": "David Brown",
                "email": "david@example.com",
                "phone": "555-0104",
                "skills": ["Python", "SQL", "ETL", "Data Warehousing"],
                "raw_text": "David Brown with 4 years of data engineering experience",
                "parsed_data": {
                    "name": "David Brown",
                    "email": "david@example.com",
                    "skills": ["Python", "SQL", "ETL", "Data Warehousing"],
                    "experience": "4 years data engineering"
                }
            },
            {
                "filename": "emma_davis.pdf",
                "full_name": "Emma Davis",
                "email": "emma@example.com",
                "phone": "555-0105",
                "skills": ["Python", "TensorFlow", "Machine Learning"],
                "raw_text": "Emma Davis with 3 years of ML engineering experience",
                "parsed_data": {
                    "name": "Emma Davis",
                    "email": "emma@example.com",
                    "skills": ["Python", "TensorFlow", "Machine Learning"],
                    "experience": "3 years ML engineering"
                }
            },
        ]

        # Add jobs
        for job_data in sample_jobs:
            job = JobListing(
                job_title=job_data["job_title"],
                company=job_data["company"],
                raw_description=job_data["raw_description"],
                parsed_data=job_data["parsed_data"],
                years_required=job_data["parsed_data"].get("years_required")
            )
            session.add(job)

        session.commit()

        # Add resumes
        for resume_data in sample_resumes:
            resume = Resume(
                filename=resume_data["filename"],
                full_name=resume_data["full_name"],
                email=resume_data["email"],
                phone=resume_data["phone"],
                skills=resume_data["skills"],
                raw_text=resume_data["raw_text"],
                parsed_data=resume_data["parsed_data"]
            )
            session.add(resume)

        session.commit()
        log.info("Test data populated successfully")

    except Exception as e:
        log.error(f"Failed to populate test data: {e}", exc_info=True)
        session.rollback()
        raise


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print(" BEDROCK POC - Database Setup ".center(80))
    print("=" * 80 + "\n")

    success = setup_database()

    if success:
        print("\n" + "=" * 80)
        print(" Setup Completed Successfully ".center(80))
        print("=" * 80)
        print("\nYou can now run the performance tests:")
        print("  python run_performance_tests.py")
        print()
        return 0
    else:
        print("\n" + "=" * 80)
        print(" Setup Failed ".center(80))
        print("=" * 80)
        print("\nPlease ensure:")
        print("  1. PostgreSQL is running")
        print("  2. Database credentials in .env are correct")
        print("  3. Check logs above for details")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
