#!/usr/bin/env python
"""Database initialization script for setting up PostgreSQL.

This script:
1. Creates the bedrock_poc database
2. Initializes all tables
3. Verifies the connection

Run this AFTER PostgreSQL is installed and before running the application.

Usage:
    python setup_database.py
"""

import os
import sys
import subprocess
from pathlib import Path

from bedrock_poc.database import create_db_engine, init_db, get_database_url
from bedrock_poc import models_db


def create_database_if_not_exists() -> bool:
    """Create the bedrock_poc database if it doesn't exist.

    Uses psql command-line tool to create the database.

    Returns:
        True if successful, False otherwise.
    """
    db_name = os.getenv("DB_NAME", "bedrock_poc")
    user = os.getenv("DB_USER", "postgres")
    host = os.getenv("DB_HOST", "localhost")

    # Connect to default postgres database to create bedrock_poc
    try:
        result = subprocess.run(
            [
                "psql",
                "-U",
                user,
                "-h",
                host,
                "-tc",
                f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and result.stdout.strip():
            print(f"✅ Database '{db_name}' already exists")
            return True

        print(f"📦 Creating database '{db_name}'...")
        result = subprocess.run(
            [
                "psql",
                "-U",
                user,
                "-h",
                host,
                "-c",
                f"CREATE DATABASE {db_name}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print(f"✅ Database '{db_name}' created successfully")
            return True
        else:
            print(f"❌ Failed to create database: {result.stderr}")
            return False

    except FileNotFoundError:
        print("❌ psql not found in PATH. Is PostgreSQL installed?")
        print("   Install PostgreSQL from: https://www.postgresql.org/download/windows/")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Database creation timed out")
        return False
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False


def initialize_tables() -> bool:
    """Create all tables in the database.

    Returns:
        True if successful, False otherwise.
    """
    try:
        print("📋 Initializing database schema...")
        engine = create_db_engine()

        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✅ Database connection verified")

        # Create tables
        init_db(engine)
        print("✅ All tables created successfully")

        return True

    except Exception as e:
        print(f"❌ Failed to initialize tables: {e}")
        print(
            "\n💡 Common issues:"
        )
        print("   1. PostgreSQL not running: Start it via Windows Services")
        print("   2. Wrong password: Check DB_PASSWORD environment variable")
        print("   3. Port mismatch: Verify PostgreSQL is on port 5432")
        return False


def verify_connection() -> bool:
    """Verify database connection and show configuration.

    Returns:
        True if connection successful, False otherwise.
    """
    try:
        print("\n🔍 Verifying database connection...")
        url = get_database_url()

        # Mask password in output
        masked_url = url.replace(os.getenv("DB_PASSWORD", "postgres"), "****")
        print(f"   URL: {masked_url}")

        engine = create_db_engine(url)

        with engine.connect() as conn:
            result = conn.execute("SELECT version()")
            version = result.scalar()
            print(f"   Version: {version}")
            print("✅ Connection successful!")
            return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def main() -> int:
    """Run database initialization workflow.

    Returns:
        0 if successful, 1 if any step failed.
    """
    print("=" * 60)
    print("🐘 PostgreSQL Database Setup for Bedrock POC")
    print("=" * 60)

    print("\n📝 Configuration:")
    print(f"   Host: {os.getenv('DB_HOST', 'localhost')}")
    print(f"   Port: {os.getenv('DB_PORT', '5432')}")
    print(f"   User: {os.getenv('DB_USER', 'postgres')}")
    print(f"   Database: {os.getenv('DB_NAME', 'bedrock_poc')}")

    # Step 1: Create database
    print("\n" + "=" * 60)
    print("STEP 1: Create Database")
    print("=" * 60)
    if not create_database_if_not_exists():
        return 1

    # Step 2: Initialize tables
    print("\n" + "=" * 60)
    print("STEP 2: Initialize Tables")
    print("=" * 60)
    if not initialize_tables():
        return 1

    # Step 3: Verify connection
    print("\n" + "=" * 60)
    print("STEP 3: Verify Connection")
    print("=" * 60)
    if not verify_connection():
        return 1

    # Success
    print("\n" + "=" * 60)
    print("✅ DATABASE SETUP COMPLETE")
    print("=" * 60)
    print("\n🚀 Next steps:")
    print("   1. Run tests: python -m pytest tests/ -v")
    print("   2. Start app: streamlit run app.py")
    print("   3. Or use CLI: python cli.py chat")

    return 0


if __name__ == "__main__":
    sys.exit(main())
