# PostgreSQL Setup Guide for Bedrock POC

**Complete guide to install, configure, and use PostgreSQL with your Bedrock POC application.**

---

## Table of Contents

1. [Installation](#installation)
2. [Verification](#verification)
3. [Database Configuration](#database-configuration)
4. [Initialize Database](#initialize-database)
5. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- Windows 11 (your system)
- Administrator access
- ~300 MB free disk space

### Step 1: Download PostgreSQL

1. Open browser and go to: **https://www.postgresql.org/download/windows/**

2. Click **"Download the installer"** (EDB Interactive Installer)

3. Select **PostgreSQL 16** (Latest stable version)

4. Download the Windows x86-64 installer (~300 MB)

### Step 2: Run the Installer

1. Double-click the downloaded `.exe` file
2. Click **"Next"** through the installation wizard

**Important Settings:**

| Setting | Value |
|---------|-------|
| Installation Directory | `C:\Program Files\PostgreSQL\16` |
| Port | `5432` |
| Superuser Password | **Set a strong password** (you'll need this!) |
| Locale | `[Default]` |
| Install pgAdmin | ✅ Yes (Optional, but recommended for GUI management) |
| Install Stack Builder | ✅ Yes (Optional, for additional tools) |

### Step 3: Complete Installation

Click **"Finish"** to complete the installation.

PostgreSQL service should now be running automatically.

---

## Verification

### Verify PostgreSQL is Running

**On Windows:**

1. Press `Windows Key + R`
2. Type `services.msc` and press Enter
3. Look for **"postgresql-x64-16"** in the list
4. Status should show **"Running"**

If not running, right-click and select **"Start"**

### Test Connection

Open PowerShell or Command Prompt and run:

```bash
psql -U postgres -h localhost -c "SELECT version();"
```

**Expected output:**
```
                                                      version
---------------------------------------------------------------------------
PostgreSQL 16.x on x86_64-pc-windows, compiled by MSVC ...
(1 row)
```

If you get a password prompt, enter the password you set during installation.

---

## Database Configuration

### Option 1: Create `.env` File (Recommended)

1. Navigate to your project directory:
   ```bash
   cd C:\Users\bhomp\Downloads\bedrock-poc\bedrock-poc
   ```

2. Copy the template:
   ```bash
   copy .env.database .env
   ```

3. Edit `.env` with your settings:
   ```bash
   # On Windows PowerShell:
   notepad .env
   ```

4. Update the password:
   ```env
   DB_USER=postgres
   DB_PASSWORD=your-postgres-password-from-installation
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=bedrock_poc
   ```

5. Save the file (Ctrl+S, then close)

### Option 2: Use Environment Variables (Windows)

**In PowerShell:**

```powershell
$env:DB_USER = "postgres"
$env:DB_PASSWORD = "your-password"
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_NAME = "bedrock_poc"
```

**To make permanent**, add to your Windows environment variables:

1. Press `Windows Key + Pause`
2. Click **"Advanced system settings"**
3. Click **"Environment Variables"**
4. Add new variables under "User variables":
   - `DB_USER` = `postgres`
   - `DB_PASSWORD` = `your-password`
   - `DB_HOST` = `localhost`
   - `DB_PORT` = `5432`
   - `DB_NAME` = `bedrock_poc`

---

## Initialize Database

### Run the Setup Script

This script will:
1. ✅ Create the `bedrock_poc` database
2. ✅ Create all tables
3. ✅ Verify the connection

**Run it:**

```bash
cd C:\Users\bhomp\Downloads\bedrock-poc\bedrock-poc
python setup_database.py
```

**Expected output:**

```
============================================================
🐘 PostgreSQL Database Setup for Bedrock POC
============================================================

📝 Configuration:
   Host: localhost
   Port: 5432
   User: postgres
   Database: bedrock_poc

============================================================
STEP 1: Create Database
============================================================
✅ Database 'bedrock_poc' already exists

============================================================
STEP 2: Initialize Tables
============================================================
✅ Database connection verified
✅ All tables created successfully

============================================================
STEP 3: Verify Connection
============================================================
🔍 Verifying database connection...
   URL: postgresql://postgres:****@localhost:5432/bedrock_poc
   Version: PostgreSQL 16.x on x86_64-pc-windows...
✅ Connection successful!

============================================================
✅ DATABASE SETUP COMPLETE
============================================================

🚀 Next steps:
   1. Run tests: python -m pytest tests/ -v
   2. Start app: streamlit run app.py
   3. Or use CLI: python cli.py chat
```

### If Setup Fails

**Error: "psql not found in PATH"**

PostgreSQL isn't in your system PATH. Try:

```bash
# Use full path
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h localhost -c "SELECT 1"
```

If that works, add PostgreSQL to PATH:

1. Press `Windows Key + Pause`
2. Click **"Advanced system settings"**
3. Click **"Environment Variables"**
4. Edit **"Path"** under System variables
5. Add: `C:\Program Files\PostgreSQL\16\bin`
6. Click **"OK"** and restart your terminal

**Error: "Connection refused"**

PostgreSQL is not running. Start it:

1. Open Services (Press `Windows + R`, type `services.msc`)
2. Find **"postgresql-x64-16"**
3. Right-click and select **"Start"**

---

## Database Schema

### Tables Created

| Table | Purpose | Records |
|-------|---------|---------|
| `conversations` | Multi-turn chat history | One per session |
| `documents` | Uploaded documents | One per file |
| `document_embeddings` | Vector embeddings | One per chunk |
| `resumes` | Parsed resume data | One per resume |
| `questions` | Q&A audit trail | One per question |

### Entity Relationships

```
Conversation (session_id)
    ├── Messages (stored as JSON)
    └── Metadata

Document (id)
    ├── Chunks (stored as JSON)
    └── DocumentEmbedding (many)
        └── Embedding vector

Resume (id)
    ├── Parsed data (JSON)
    └── Skills (array)

Question (session_id)
    ├── Document reference (optional)
    └── Answer + metadata
```

---

## Using the Database

### In Your Python Code

**Example: Save a conversation**

```python
from bedrock_poc.database import get_session
from bedrock_poc.models_db import Conversation

for session in get_session():
    conv = Conversation(
        session_id="abc-123",
        messages=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ],
        model_id="claude-3-5-sonnet"
    )
    session.add(conv)
    session.commit()
```

**Example: Query conversations**

```python
from bedrock_poc.database import get_session
from bedrock_poc.models_db import Conversation
from uuid import UUID

session_id = UUID("abc-123")

for session in get_session():
    conversations = session.query(Conversation).filter(
        Conversation.session_id == session_id
    ).all()
    
    for conv in conversations:
        print(f"Session {conv.session_id}: {len(conv.messages)} messages")
```

**Example: Store a resume**

```python
from bedrock_poc.database import get_session
from bedrock_poc.models_db import Resume

for session in get_session():
    resume = Resume(
        filename="john_doe_resume.pdf",
        raw_text="...",
        parsed_data={
            "full_name": "John Doe",
            "email": "john@example.com",
            "skills": ["Python", "AWS"]
        },
        full_name="John Doe",
        email="john@example.com"
    )
    session.add(resume)
    session.commit()
```

---

## Management

### Access Database with pgAdmin (GUI)

1. PostgreSQL installation includes pgAdmin 4
2. Open browser to: **http://localhost:5050**
3. Login with email set during installation
4. Connect to local server
5. Browse tables and data

### Access Database with psql (CLI)

```bash
# Connect to bedrock_poc database
psql -U postgres -d bedrock_poc -h localhost

# List tables
\dt

# Query conversations
SELECT session_id, created_at, array_length(messages, 1) as msg_count FROM conversations LIMIT 5;

# Query resumes
SELECT full_name, email, created_at FROM resumes;

# Exit
\q
```

### Backup Database

```bash
# Backup to file
pg_dump -U postgres -d bedrock_poc -h localhost > backup.sql

# Restore from backup
psql -U postgres -d bedrock_poc -h localhost < backup.sql
```

---

## Troubleshooting

### PostgreSQL Won't Start

**Symptom:** Cannot connect to PostgreSQL

**Solution:**

1. Open Services (`services.msc`)
2. Find **"postgresql-x64-16"**
3. If status is "Stopped", right-click → **"Start"**
4. If "Start" is grayed out, restart your computer

### Wrong Password

**Symptom:** `FATAL: password authentication failed`

**Solution:**

1. Go to Windows Services (search "services")
2. Stop PostgreSQL service
3. Right-click PostgreSQL → Properties
4. Note the "Log on as" account (usually "NT AUTHORITY\NetworkService")
5. Reinstall PostgreSQL with correct password
6. Update `.env` file with new password

### Database Already Exists

**Symptom:** "Database bedrock_poc already exists"

**Solution:**

```bash
# Drop existing database (WARNING: deletes all data!)
psql -U postgres -h localhost -c "DROP DATABASE bedrock_poc;"

# Then run setup again
python setup_database.py
```

### Connection Timeout

**Symptom:** `could not connect to server: Connection refused`

**Cause:** PostgreSQL not running or wrong host/port

**Solution:**

1. Verify PostgreSQL is running in Services
2. Check `.env` file has correct values:
   ```
   DB_HOST=localhost
   DB_PORT=5432
   ```
3. Test connection manually:
   ```bash
   psql -U postgres -h localhost -p 5432 -c "SELECT 1"
   ```

### Port Already in Use

**Symptom:** `FATAL: could not bind IPv4 socket`

**Cause:** Another PostgreSQL instance or different service on port 5432

**Solution:**

Option 1: Stop other service on port 5432
```bash
netstat -ano | findstr :5432
# Get PID from output
taskkill /PID <PID> /F
```

Option 2: Run PostgreSQL on different port

In `.env`:
```
DB_PORT=5433
```

Then reconfigure PostgreSQL installation to use port 5433

---

## Next Steps

### 1. Verify Setup

```bash
python setup_database.py
```

### 2. Run Tests

```bash
python -m pytest tests/ -v
```

### 3. Start Application

```bash
# Streamlit UI
streamlit run app.py

# Or CLI
python cli.py chat
```

### 4. Check Database

Open pgAdmin to browse tables:
- http://localhost:5050

---

## References

- PostgreSQL Official: https://www.postgresql.org
- EDB Installer: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
- pgAdmin: https://www.pgadmin.org
- SQLAlchemy Docs: https://docs.sqlalchemy.org
- Alembic (Migrations): https://alembic.sqlalchemy.org

---

**PostgreSQL Setup Complete!** 🐘✅

Your Bedrock POC is now ready for persistent database storage.
