"""Create the job_queue table for testing."""

import sqlite3

conn = sqlite3.connect('bedrock_poc.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS job_queue (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    job_id TEXT UNIQUE NOT NULL,
    job_description TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    result JSON,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    metadata_json JSON
)
''')

conn.commit()
conn.close()
print('[OK] job_queue table created')
