# Clean Environment Setup Guide

**Status:** 📋 Complete Setup Instructions  
**Date:** 2026-08-10  
**Python Version:** 3.11 or 3.12 (stable, production-ready)  
**Difficulty:** Easy | **Time:** 20-30 minutes

---

## ⚠️ Important Note

**If you previously had a broken environment (Python 3.14):**
1. Delete the old `.venv` folder completely
2. Follow the steps below to create a fresh environment
3. This ensures a clean, reproducible setup

---

## Prerequisites

Before starting, ensure you have:
- ✅ **Python 3.11 or 3.12** installed (NOT 3.14, NOT 3.10)
- ✅ **Git** for version control
- ✅ **AWS Account** with Bedrock access
- ✅ **PostgreSQL 14+** (for database support)
- ✅ **Text editor** (VS Code, Sublime, etc.)

### Verify Python Installation

```powershell
# Windows - Run in PowerShell or CMD
python --version
# Expected output: Python 3.11.x or Python 3.12.x

# Verify pip is available
pip --version
# Expected output: pip x.x.x from C:\...\Python311\lib\site-packages
```

---

## Step 1: Install Python (If Not Installed)

### Windows Users

1. Download Python 3.12 from https://www.python.org/downloads/
2. Run the installer
3. **IMPORTANT:** Check "Add Python to PATH" ✅
4. Check "Install pip" ✅
5. Click "Install Now"
6. Wait for completion (~2 minutes)

### Verify Installation
```powershell
python --version
# Should show: Python 3.12.x
```

---

## Step 2: Remove Old Virtual Environment (If Exists)

```powershell
# Navigate to project directory
cd C:\Users\YourName\Downloads\bedrock-poc\bedrock-poc

# Delete old venv if it exists
if (Test-Path .venv) { 
    Remove-Item -Recurse -Force .venv
    Write-Host "Old venv removed ✅"
} else {
    Write-Host "No existing venv found"
}
```

---

## Step 3: Create Fresh Virtual Environment

```powershell
# Create new virtual environment
python -m venv .venv

# Activate it (Windows)
.\.venv\Scripts\Activate.ps1

# Expected: You should see (.venv) at the start of your prompt
# If you get an execution policy error, see Troubleshooting section below
```

---

## Step 4: Upgrade pip

```powershell
# Make sure venv is activated: (.venv) should show in prompt
python -m pip install --upgrade pip

# Verify upgrade
pip --version
# Expected: pip 24.x or higher
```

---

## Step 5: Install Project Dependencies

```powershell
# Install all required packages from requirements.txt
pip install -r requirements.txt

# This will install:
# - boto3 (AWS SDK)
# - streamlit (Web UI)
# - pydantic (Data validation)
# - pypdf (PDF parsing)
# - psycopg2-binary (PostgreSQL driver)
# - sqlalchemy (ORM)
# - alembic (Database migrations)
# - pytest (Testing)

# Installation will take 5-10 minutes. Please wait...
```

---

## Step 6: Verify Installation

```powershell
# Check for any dependency conflicts
pip check

# Expected output:
# No broken requirements found.

# OR if issues found, they will be listed
# Common issue: psycopg2-binary may need compiler
# Solution: See Troubleshooting section
```

---

## Step 7: Configure AWS Credentials

You need AWS credentials to use Bedrock. Choose one method:

### Method A: AWS CLI (Recommended)

```powershell
# Configure AWS
aws configure

# When prompted, enter:
# AWS Access Key ID: [your-key]
# AWS Secret Access Key: [your-secret]
# Default region: us-east-1
# Default output format: json
```

### Method B: Environment Variables

```powershell
# Set environment variables (Windows PowerShell)
$env:AWS_ACCESS_KEY_ID = "your-access-key"
$env:AWS_SECRET_ACCESS_KEY = "your-secret-key"
$env:AWS_REGION = "us-east-1"
```

### Method C: .env File (Easiest)

Create file `.env` in project root:
```
# AWS Bedrock Configuration
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# PostgreSQL Database Configuration
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bedrock_poc
```

⚠️ **Security Note:** Never commit `.env` to Git. It's in `.gitignore` for security.

---

## Step 8: Configure PostgreSQL Database

### Windows - Install PostgreSQL

1. Download from https://www.postgresql.org/download/windows/
2. Run installer: `postgresql-16-windows-x64.exe`
3. Installation steps:
   - Accept license
   - Choose directory (default OK)
   - Choose components: **uncheck** "Stack Builder" (unchecked)
   - Data directory: default
   - Superuser password: **Write this down!**
   - Port: 5432 (default)
   - Locale: Default
   - Pre-installation check: OK
   - Ready to install: Next
4. Wait for installation (~5 minutes)

### Create Application Database

```powershell
# Connect to PostgreSQL with psql
psql -U postgres

# At the PostgreSQL prompt (postgres=#), run:
CREATE DATABASE bedrock_poc;

# Verify creation
\l

# Exit
\q
```

### Verify Database Connection

```powershell
# Make sure venv is activated
python test_db_connection.py

# Expected output:
# ✅ PostgreSQL Connection Successful!
# ✅ Version: PostgreSQL 16.x...
```

---

## Step 9: Initialize Database Schema

```powershell
# Create all tables (one-time setup)
python -c "from bedrock_poc.database import init_db; init_db(); print('✅ Database initialized')"

# Alternative using Python REPL
python
>>> from bedrock_poc.database import init_db
>>> init_db()
>>> print('✅ Database initialized')
>>> exit()
```

---

## Step 10: Run Tests

```powershell
# Ensure venv is activated
# Run all tests
python -m pytest tests/ -v

# Expected output:
# ===== test session starts =====
# tests/test_use_cases.py::test_summarize_builds_request_and_returns_text PASSED
# tests/test_use_cases.py::test_summarize_rejects_empty_document PASSED
# ... more tests ...
# ===== 6 passed in 0.50s =====
```

---

## Step 11: Run the Application

### Option A: Streamlit Web UI (Recommended)

```powershell
# Make sure venv is activated
streamlit run app.py

# Expected output:
# You can now view your Streamlit app in your browser.
# Local URL: http://localhost:8501
# Network URL: http://192.168.x.x:8501

# Open browser at http://localhost:8501
# You should see the app with Chat, Summarize, Q&A, Parse Resume tabs
```

### Option B: CLI Commands

```powershell
# Chat (interactive)
python cli.py chat

# Summarize a document
python cli.py summarize --file large_document.txt

# Ask questions about a document
python cli.py ask --file large_document.txt --question "What is this?"

# Parse a resume
python cli.py parse --file resume.pdf

# Q&A with RAG
python cli.py ask --file large_document.txt --question "What are key points?" --use-rag
```

---

## Troubleshooting

### Issue: "Python was not found"

**Cause:** Python not installed or not in PATH  
**Solution:**
```powershell
# Check Python is installed
where python

# If not found, install Python 3.12 from python.org
# Make sure to check "Add Python to PATH" during installation
# Restart PowerShell after installation
```

---

### Issue: "venv activation fails - execution policy error"

**Error Message:**
```
cannot be loaded because running scripts is disabled on this system
```

**Solution:**
```powershell
# Set execution policy for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activation again
.\.venv\Scripts\Activate.ps1
```

---

### Issue: "pip install fails for psycopg2-binary"

**Error:** `error: Microsoft Visual C++ 14.0 or greater is required`

**Solution:**
```powershell
# Option 1: Install pre-built wheel (usually works)
pip install --only-binary :all: psycopg2-binary

# Option 2: Install C++ build tools
# Download and install: Visual Studio Build Tools
# https://visualstudio.microsoft.com/downloads/
# Choose: "Desktop development with C++"
```

---

### Issue: "ModuleNotFoundError: No module named 'streamlit'"

**Cause:** Virtual environment not activated  
**Solution:**
```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# (.venv) should appear in prompt

# Reinstall dependencies
pip install -r requirements.txt
```

---

### Issue: "PostgreSQL Connection Failed"

**Error:** `FATAL: password authentication failed`

**Solutions:**
1. Check `.env` has correct `DB_PASSWORD`
2. Check PostgreSQL is running
3. Reset PostgreSQL password:
```powershell
# Windows - Open Command Prompt as Admin
# Stop PostgreSQL service
net stop postgresql-x64-16

# Start it again
net start postgresql-x64-16

# Connect and reset password
psql -U postgres
# At prompt:
# ALTER USER postgres WITH PASSWORD 'newpassword';
# \q
```

---

### Issue: "Port 8501 already in use"

**Solution:**
```powershell
# Run on different port
streamlit run app.py --server.port 8502

# Access at http://localhost:8502
```

---

### Issue: "Database table 'conversations' does not exist"

**Cause:** Schema not initialized  
**Solution:**
```powershell
# Initialize database schema
python -c "from bedrock_poc.database import init_db; init_db()"

# Verify tables were created
psql -U postgres -d bedrock_poc
# At prompt:
# \dt
# \q
```

---

## Verification Checklist

After setup, verify everything works:

- [ ] Python version is 3.11 or 3.12: `python --version`
- [ ] Virtual environment is activated: `(.venv)` shows in prompt
- [ ] Dependencies installed: `pip list | grep streamlit`
- [ ] AWS credentials work: `aws sts get-caller-identity`
- [ ] Bedrock model access: `aws bedrock list-foundation-models`
- [ ] PostgreSQL running: `psql -U postgres -c "SELECT 1"`
- [ ] Database exists: `psql -U postgres -l | grep bedrock_poc`
- [ ] All tests pass: `python -m pytest tests/ -v`
- [ ] Streamlit app runs: `streamlit run app.py` (press Ctrl+C to stop)

---

## Quick Start Summary

```powershell
# 1. Navigate to project
cd C:\Users\YourName\Downloads\bedrock-poc\bedrock-poc

# 2. Remove old venv if exists
if (Test-Path .venv) { Remove-Item -Recurse -Force .venv }

# 3. Create and activate venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install dependencies
pip install -r requirements.txt

# 6. Configure .env file with AWS and DB credentials

# 7. Test PostgreSQL connection
python test_db_connection.py

# 8. Initialize database schema
python -c "from bedrock_poc.database import init_db; init_db()"

# 9. Run tests
python -m pytest tests/ -v

# 10. Start Streamlit app
streamlit run app.py
```

---

## Next Steps

Once the environment is fully operational:

1. ✅ Complete Job Description Parsing module
2. ✅ Implement advanced matching engine and semantic ranking
3. ✅ Develop skills gap analysis feature
4. ✅ Continue Candidate Search and Match Results APIs
5. ✅ Expand unit and integration test coverage
6. ✅ Update technical and API documentation

---

## Git Workflow

```powershell
# Check status
git status

# Add changes
git add .

# Commit
git commit -m "fix: Resolve Python environment and dependency issues"

# Push to remote
git push origin main
```

---

## Support & Resources

**If you encounter issues:**
1. Check this troubleshooting section
2. Review error messages carefully
3. Check virtual environment is activated
4. Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
5. Clear cache: `rm -rf .pytest_cache __pycache__`

**Related Documentation:**
- `LOCAL_SETUP.md` — Original setup guide
- `POSTGRES_SETUP.md` — Detailed PostgreSQL setup
- `README.md` — Project overview
- `ARCHITECTURE.md` — System design

---

**Environment Status:** READY FOR FRESH SETUP ✅  
**Last Updated:** 2026-08-10  
**Prepared By:** Claude Code
