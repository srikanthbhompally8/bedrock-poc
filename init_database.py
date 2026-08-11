#!/usr/bin/env python
"""Initialize the database with credentials from .env file."""

from dotenv import load_dotenv
from bedrock_poc.database import init_db

# Load environment variables from .env
load_dotenv()

# Initialize the database
try:
    init_db()
    print("✅ Database schema initialized successfully")
except Exception as e:
    print(f"❌ Error initializing database: {e}")
    raise
