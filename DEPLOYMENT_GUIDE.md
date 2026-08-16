# Deployment Guide

**Version:** 1.0.0  
**Last Updated:** 2026-08-14  
**Status:** Production Ready

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Application Deployment](#application-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Production Checklist](#production-checklist)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **OS:** Windows 11 / macOS / Linux
- **Python:** 3.11 or 3.12 (LTS)
- **PostgreSQL:** 14+ (optional for demo)
- **Git:** 2.30+
- **RAM:** 4GB minimum, 8GB recommended
- **Disk:** 5GB free space

### Software Installation

```bash
# 1. Install Python 3.12 from https://python.org
# 2. Install PostgreSQL from https://postgresql.org (optional)
# 3. Clone the repository
git clone https://github.com/srikanthbhompally8/bedrock-poc.git
cd bedrock-poc
```

---

## Environment Setup

### Step 1: Create Virtual Environment

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install from requirements.txt
pip install -r requirements.txt

# Verify installation
pip check
```

### Step 3: Configure Environment Variables

Create `.env` file in project root:

```bash
# AWS Bedrock Configuration
BEDROCK_MODEL_ID=us.anthropic.claude-opus-5-20250514-v1:0
AWS_REGION=us-east-2
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# PostgreSQL Database Configuration (optional)
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bedrock_poc
```

### Step 4: Verify AWS Credentials

```bash
# Test AWS connection
aws sts get-caller-identity

# Expected output:
# {
#     "UserId": "...",
#     "Account": "123456789",
#     "Arn": "arn:aws:iam::..."
# }
```

---

## Database Setup

### Option A: Local PostgreSQL

#### 1. Install PostgreSQL

**Windows:**
```bash
# Download from postgresql.org
# During installation, note the superuser password
# Default port: 5432
```

**macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### 2. Create Database & User

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE bedrock_poc;

# Create user
CREATE USER bedrock_user WITH PASSWORD 'secure_password_here';

# Grant privileges
ALTER DATABASE bedrock_poc OWNER TO bedrock_user;
GRANT ALL PRIVILEGES ON DATABASE bedrock_poc TO bedrock_user;

# Exit
\q
```

#### 3. Initialize Schema

```bash
# Activate venv first
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows

# Initialize database
python -c "from bedrock_poc.database import init_db; init_db()"

# Verify tables created
psql -U bedrock_user -d bedrock_poc

# At the prompt:
\dt

# You should see: conversations, documents, questions, resumes, etc.
\q
```

### Option B: Cloud Database (AWS RDS)

```bash
# Create RDS PostgreSQL instance via AWS console
# Use these settings:
# - Engine: PostgreSQL 14.x
# - Instance class: db.t3.micro (development) or db.t3.small (production)
# - Storage: 20GB SSD
# - Publicly accessible: No (use VPC security groups)

# Update .env with RDS endpoint
DB_HOST=your-rds-endpoint.us-east-2.rds.amazonaws.com
DB_USER=postgres
DB_PASSWORD=your-master-password
DB_PORT=5432
DB_NAME=bedrock_poc

# Run initialization
python -c "from bedrock_poc.database import init_db; init_db()"
```

---

## Application Deployment

### Local Development

```bash
# 1. Activate virtual environment
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate

# 2. Run tests
python -m pytest tests/ -v

# 3. Start application
streamlit run app.py

# 4. Open browser
# http://localhost:8501
```

### Staging Deployment

```bash
# 1. Create staging directory
mkdir -p /var/www/bedrock-poc-staging
cd /var/www/bedrock-poc-staging

# 2. Clone repository
git clone https://github.com/srikanthbhompally8/bedrock-poc.git .

# 3. Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
# Edit .env with staging credentials

# 6. Initialize database
python -c "from bedrock_poc.database import init_db; init_db()"

# 7. Run tests
python -m pytest tests/ -v --tb=short

# 8. Start application
nohup streamlit run app.py --server.port 8501 > logs/app.log 2>&1 &
```

### Production Deployment

```bash
# 1. Use gunicorn for ASGI server (not streamlit)
pip install gunicorn

# 2. Create production directory
mkdir -p /var/www/bedrock-poc
cd /var/www/bedrock-poc

# 3. Deploy latest release
git clone --branch main https://github.com/srikanthbhompally8/bedrock-poc.git .

# 4. Setup production environment
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configure production .env
# Set with production AWS credentials, RDS endpoint, etc.

# 6. Run migrations
python -c "from bedrock_poc.database import init_db; init_db()"

# 7. Start with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# 8. Configure reverse proxy (nginx)
# See NGINX_CONFIG.md
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501')"

# Run application
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: bedrock_poc
      POSTGRES_USER: bedrock_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bedrock_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build: .
    environment:
      AWS_REGION: ${AWS_REGION}
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      DB_HOST: postgres
      DB_USER: bedrock_user
      DB_PASSWORD: ${DB_PASSWORD}
      DB_NAME: bedrock_poc
    ports:
      - "8501:8501"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./bedrock_poc:/app/bedrock_poc
```

### Deploy with Docker

```bash
# 1. Build image
docker build -t bedrock-poc:1.0.0 .

# 2. Run with docker-compose
docker-compose up -d

# 3. Check logs
docker-compose logs -f app

# 4. Stop
docker-compose down
```

---

## Production Checklist

### Before Going Live

- [ ] **Database**
  - [ ] PostgreSQL 14+ configured
  - [ ] Automated daily backups enabled
  - [ ] Connection pooling configured (pgBouncer)
  - [ ] Indexes optimized
  
- [ ] **Security**
  - [ ] AWS credentials rotated
  - [ ] .env file not in git repo
  - [ ] Database password is 20+ characters
  - [ ] SSL/TLS enabled for database
  - [ ] API keys stored in secrets manager
  
- [ ] **Monitoring**
  - [ ] Error logging configured (e.g., Sentry)
  - [ ] Performance monitoring active
  - [ ] Database query logs enabled
  - [ ] Application logs centralized
  
- [ ] **Testing**
  - [ ] All 52 unit tests passing
  - [ ] Integration tests passing
  - [ ] Load testing completed
  - [ ] Security audit completed
  
- [ ] **Documentation**
  - [ ] API documentation published
  - [ ] Database schema documented
  - [ ] Runbook for common operations
  - [ ] Disaster recovery plan
  
- [ ] **Deployment**
  - [ ] CI/CD pipeline configured
  - [ ] Blue-green deployment ready
  - [ ] Rollback procedure tested
  - [ ] Health checks configured

---

## Scaling Considerations

### Horizontal Scaling

```bash
# Use load balancer (AWS ELB / nginx)
# Run multiple app instances:

# Instance 1
streamlit run app.py --server.port 8501

# Instance 2
streamlit run app.py --server.port 8502

# Instance 3
streamlit run app.py --server.port 8503

# nginx load balancing across 8501-8503
```

### Vertical Scaling

- **Database:** Upgrade RDS instance type
- **Application:** Increase Streamlit worker count
- **Caching:** Implement Redis for session data

### Database Optimization

```sql
-- Monthly vacuum and analyze
VACUUM ANALYZE;

-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Reindex if needed
REINDEX DATABASE bedrock_poc;
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
psql -h localhost -U bedrock_user -d bedrock_poc -c "SELECT 1"

# Check PostgreSQL service
sudo systemctl status postgresql

# View connection logs
sudo tail -f /var/log/postgresql/postgresql.log
```

### Application Startup Issues

```bash
# Clear cache
rm -rf .streamlit

# Check Python version
python --version  # Should be 3.11+

# Verify all dependencies
pip check

# Run with verbose output
streamlit run app.py --logger.level=debug
```

### Performance Issues

```bash
# Monitor database connections
psql -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname"

# Check slow queries
psql -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 5"

# Monitor application memory
ps aux | grep streamlit
```

---

## Support

- **Documentation:** See README.md
- **Issues:** https://github.com/srikanthbhompally8/bedrock-poc/issues
- **API Docs:** See API_DOCUMENTATION.md
- **Database Docs:** See DATABASE_SCHEMA.md

---

**Version:** 1.0.0  
**Last Updated:** 2026-08-14  
**Status:** Production Ready ✅
