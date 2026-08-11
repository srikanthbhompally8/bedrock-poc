"""Test PostgreSQL connection with credentials from .env"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD')
    )
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print('✅ PostgreSQL Connection Successful!')
    print(f'✅ Version: {version[0][:80]}')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'❌ Connection Failed: {e}')
    print()
    print('Make sure your .env file has the correct DB_PASSWORD')
