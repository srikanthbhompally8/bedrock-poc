# Quick Start: PostgreSQL Setup (5 Minutes)

**Complete step-by-step guide to get PostgreSQL running with your Bedrock POC.**

---

## Quick Summary

You now have:
- ✅ psycopg2-binary (PostgreSQL driver)
- ✅ SQLAlchemy (ORM)
- ✅ Alembic (migrations)
- ✅ Database models created
- ✅ Automated setup script

All you need to do is:
1. Download & install PostgreSQL
2. Run the setup script
3. Start using the app

---

## STEP 1: Download PostgreSQL (2 minutes)

### Option A: Automatic (If you have internet browser)

1. Go to: **https://www.postgresql.org/download/windows/**
2. Click **"Download the installer"** (EDB version)
3. Choose **PostgreSQL 16** for Windows x64
4. Download the `.exe` file (~300 MB)

### Option B: Direct Download

**Download link:** https://www.enterprisedb.com/downloads/postgres-postgresql-downloads

Select PostgreSQL 16, Windows x64 bit.

---

## STEP 2: Install PostgreSQL (2 minutes)

1. **Double-click** the downloaded `.exe` file
2. Click **"Next"** through each step
3. **IMPORTANT: When prompted for "Password":**
   - Enter a strong password (you'll need this!)
   - Example: `MyPostgres123!`
   - **WRITE IT DOWN** - you'll use it in the next step

4. Keep all other settings as default:
   - Port: `5432` ✅
   - Superuser: `postgres` ✅
   - Locale: `[Default]` ✅

5. Click **"Finish"**

PostgreSQL is now installed and running! ✅

---

## STEP 3: Configure Your App (1 minute)

### Create .env File

1. Open PowerShell in your project directory:
   ```bash
   cd C:\Users\bhomp\Downloads\bedrock-poc\bedrock-poc
   ```

2. Copy the template:
   ```bash
   copy .env.database .env
   ```

3. Edit the file:
   ```bash
   notepad .env
   ```

4. **Update the password line:**
   ```env
   DB_PASSWORD=MyPostgres123!
   ```
   (Replace with the password you set during PostgreSQL installation)

5. Save: `Ctrl+S`, then close

**Your .env should look like:**
```env
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
AWS_REGION=us-east-1

DB_USER=postgres
DB_PASSWORD=MyPostgres123!
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bedrock_poc
```

---

## STEP 4: Initialize Database (1 minute)

Run the setup script:

```bash
python setup_database.py
```

**You should see:**
```
============================================================
🐘 PostgreSQL Database Setup for Bedrock POC
============================================================

✅ Database 'bedrock_poc' already exists
✅ Database connection verified
✅ All tables created successfully
✅ Connection successful!

============================================================
✅ DATABASE SETUP COMPLETE
============================================================
```

**If you see errors, see "Troubleshooting" section below.**

---

## Done! 🎉

Your PostgreSQL database is now integrated and ready to use!

### Next Steps:

**Option 1: Run the application**
```bash
streamlit run app.py
```
Then open: http://localhost:8501

**Option 2: Use the CLI**
```bash
python cli.py chat
```

**Option 3: Run tests**
```bash
python -m pytest tests/ -v
```

---

## Troubleshooting

### Problem: "Connection refused"

**PostgreSQL is not running.**

Solution:
1. Press `Windows + R`
2. Type: `services.msc`
3. Find: `postgresql-x64-16`
4. Right-click → **Start**

Wait 10 seconds, then try `setup_database.py` again.

### Problem: "Authentication failed"

**Wrong PostgreSQL password in .env**

Solution:
1. Check you set the right password during PostgreSQL install
2. Update `.env` with correct password
3. Try again

### Problem: "psql not found"

**PostgreSQL not in system PATH**

Solution: Use full path:
```bash
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "SELECT 1"
```

If that works, add to PATH (see POSTGRES_SETUP.md for details).

### Problem: "Port 5432 already in use"

**Another PostgreSQL or service on that port**

Solution:
1. Find what's using port 5432:
   ```bash
   netstat -ano | findstr :5432
   ```
2. Either stop that service or run PostgreSQL on different port (5433)

---

## Verify It Works

**Test in PowerShell:**

```bash
cd C:\Users\bhomp\Downloads\bedrock-poc\bedrock-poc

# Should show database is working
python setup_database.py

# Should pass all tests
python -m pytest tests/ -v

# Should start Streamlit on http://localhost:8501
streamlit run app.py
```

---

## What Just Happened?

You now have:

### Database Engine
- `bedrock_poc/database.py` - Connection management & session factory

### Data Models
- `bedrock_poc/models_db.py` - SQLAlchemy ORM tables:
  - `Conversation` - Chat history (with session tracking)
  - `Document` - Uploaded files + chunks
  - `DocumentEmbedding` - Vector embeddings for RAG
  - `Resume` - Parsed resume data
  - `Question` - Q&A audit trail

### Setup Script
- `setup_database.py` - Automated database initialization

### Documentation
- `POSTGRES_SETUP.md` - Complete setup guide
- `QUICK_START_POSTGRES.md` - This file

### Updated Dependencies
- `requirements.txt` - Now includes:
  - psycopg2-binary 2.9+
  - sqlalchemy 2.0+
  - alembic 1.12+

---

## Database Tables

After setup, your database contains:

| Table | Stores |
|-------|--------|
| `conversations` | Multi-turn chat history |
| `documents` | Uploaded documents + chunks |
| `document_embeddings` | Vector embeddings for RAG search |
| `resumes` | Parsed resume data (JSON) |
| `questions` | Q&A questions and answers (audit trail) |

All data persists between app restarts. ✅

---

## Using the Database in Code

Your app can now save/load data:

```python
from bedrock_poc.database import get_session
from bedrock_poc.models_db import Conversation

# Save a conversation
for session in get_session():
    conv = Conversation(
        session_id="user-123",
        messages=[...],
        model_id="claude-3-5-sonnet"
    )
    session.add(conv)
    session.commit()

# Load conversations
for session in get_session():
    convs = session.query(Conversation).all()
    for conv in convs:
        print(conv.messages)
```

---

## Need Help?

See: `POSTGRES_SETUP.md` for complete documentation

Key sections:
- Installation troubleshooting
- Database management (pgAdmin, psql)
- Backup/restore procedures
- Using database in Python code

---

**You're all set! PostgreSQL is now part of your Bedrock POC.** 🐘✅

Run `python setup_database.py` to initialize, then start your app!
