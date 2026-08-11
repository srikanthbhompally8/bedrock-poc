# PostgreSQL Setup - Quick Reference

**Status:** Production-Ready PostgreSQL 14+  
**Time to Setup:** 5-10 minutes  

---

## 1. Install PostgreSQL (Windows)

```powershell
# Download from: https://www.postgresql.org/download/windows/
# Run: postgresql-16-windows-x64.exe

# During installation:
# ✅ Accept license
# ✅ Installation directory: C:\Program Files\PostgreSQL\16
# ✅ Components: uncheck "Stack Builder" and "LaunchPad"
# ✅ Data directory: Default
# ✅ Superuser password: Set a strong password!
# ✅ Port: 5432 (default)
# ✅ Locale: Default
# ✅ Complete installation

# After installation, verify:
psql --version
# Expected: psql (PostgreSQL) 16.x
```

---

## 2. Create Application Database

```powershell
# Connect to PostgreSQL as superuser
psql -U postgres

# At the postgres=# prompt, run:
CREATE DATABASE bedrock_poc;
CREATE USER bedrock_user WITH PASSWORD 'your-secure-password';
ALTER DATABASE bedrock_poc OWNER TO bedrock_user;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE bedrock_poc TO bedrock_user;

# Exit
\q
```

---

## 3. Configure .env File

Create `.env` in project root:

```
# AWS Configuration
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# PostgreSQL Configuration
DB_USER=bedrock_user
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bedrock_poc
```

---

## 4. Test Connection

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Test connection
python test_db_connection.py

# Expected output:
# ✅ PostgreSQL Connection Successful!
# ✅ Version: PostgreSQL 16.x...
```

---

## 5. Initialize Database Schema

```powershell
# From project root (venv activated)
python -c "from bedrock_poc.database import init_db; init_db()"

# Verify tables created
psql -U bedrock_user -d bedrock_poc

# At prompt:
\dt
# Should show:
# conversations
# documents
# document_embeddings
# questions
# resumes

\q
```

---

## 6. Verify Installation

```powershell
# Check PostgreSQL service is running
Get-Service -Name "postgresql-x64-16" | Select-Object Status

# Expected: Status should be "Running"

# Test data insertion
psql -U bedrock_user -d bedrock_poc -c "SELECT COUNT(*) FROM conversations;"

# Expected: 0 (empty table)
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| "psql: command not found" | PostgreSQL not in PATH. Restart terminal after install. |
| "password authentication failed" | Check .env has correct DB_PASSWORD |
| "database does not exist" | Run: `CREATE DATABASE bedrock_poc;` |
| "permission denied" | Grant privileges: `ALTER DATABASE bedrock_poc OWNER TO bedrock_user;` |
| "tables don't exist" | Run: `python -c "from bedrock_poc.database import init_db; init_db()"` |

---

## Useful PostgreSQL Commands

```powershell
# Connect to database
psql -U bedrock_user -d bedrock_poc

# List tables
\dt

# Show table structure
\d conversations

# Run SQL query
SELECT COUNT(*) FROM conversations;

# Exit
\q

# Backup database
pg_dump -U bedrock_user bedrock_poc > bedrock_poc_backup.sql

# Restore database
psql -U bedrock_user bedrock_poc < bedrock_poc_backup.sql

# Drop database (careful!)
DROP DATABASE bedrock_poc;
```

---

## Windows Service Management

```powershell
# Check service status
Get-Service -Name "postgresql-x64-16"

# Stop service
net stop postgresql-x64-16

# Start service
net start postgresql-x64-16

# Check if running
netstat -an | findstr 5432
# Should show: LISTENING on 127.0.0.1:5432
```

---

## Production Recommendations

- ✅ Use strong passwords (min 20 characters)
- ✅ Regular backups: `pg_dump -U bedrock_user bedrock_poc > backup.sql`
- ✅ Monitor disk space: Large embeddings need storage
- ✅ Update PostgreSQL regularly: security patches
- ✅ Use SSL connections for remote deployments
- ✅ Enable query logging: set `log_statement = 'all'` in postgresql.conf

---

**Status:** Ready to setup ✅
