# Production Configuration Guide

**Document Version:** 1.0  
**Last Updated:** 2026-08-20  
**Status:** Phase 4 - Production Readiness

---

## Overview

This guide provides comprehensive instructions for configuring the Bedrock POC application for production deployment. It covers environment configuration, database setup, security hardening, and deployment considerations.

---

## Table of Contents

1. [Configuration System](#configuration-system)
2. [Environment Variables](#environment-variables)
3. [Environment-Specific Setup](#environment-specific-setup)
4. [Database Configuration](#database-configuration)
5. [Security Configuration](#security-configuration)
6. [Monitoring & Logging Setup](#monitoring--logging-setup)
7. [AWS Secrets Manager Integration](#aws-secrets-manager-integration)
8. [Validation & Health Checks](#validation--health-checks)
9. [Troubleshooting](#troubleshooting)

---

## Configuration System

### Architecture

The Bedrock POC uses a layered configuration system built on Pydantic BaseSettings:

```
Environment Variables (.env files)
    ↓
Pydantic Settings Classes
    ├── DatabaseSettings
    ├── RedisSettings
    ├── BedrockSettings
    ├── AuthSettings
    ├── LoggingSettings
    └── MonitoringSettings
    ↓
Validated Settings Instance (get_settings())
    ↓
Application Code
```

### Key Features

- **Type Safety:** All configuration values are validated with Pydantic
- **Environment-Specific:** Different configs for dev/staging/production
- **Secrets Management:** Sensitive values can come from AWS Secrets Manager
- **Validation:** All settings validated at startup (fail fast principle)
- **Hot Reload:** Settings can be reloaded without restarting app
- **Caching:** Settings instance is cached using `@lru_cache`

### Configuration Files

```
bedrock-poc/
├── .env                    # Local development (git ignored)
├── .env.example            # Example for developers
├── .env.template           # Comprehensive template with documentation
├── .env.development        # Development environment
├── .env.staging            # Staging environment
├── .env.production         # Production environment (git ignored)
└── bedrock_poc/config/
    ├── __init__.py
    ├── settings.py         # Main Pydantic settings classes
    └── database.py         # Database connection management
```

---

## Environment Variables

### Application Settings

```bash
# Application identity
APP_NAME=Bedrock POC              # Application name for logs/metrics
ENVIRONMENT=production             # Environment: development|staging|production
DEBUG=false                        # Enable debug mode
API_VERSION=v1                     # API version for versioning
API_PREFIX=/api                    # URL prefix for API routes
```

### Server Settings

```bash
# Server configuration
HOST=0.0.0.0                      # Bind address (0.0.0.0 for production)
PORT=8000                         # Server port
WORKERS=8                         # Number of worker processes
RELOAD=false                      # Auto-reload on code changes (dev only)

# Worker calculation for production: WORKERS = (2 * CPU_CORES) + 1
# Example: 4-core machine → 9 workers
```

### Database Settings

```bash
# PostgreSQL connection
DB_HOST=bedrock-prod-rds.xxxxx.rds.amazonaws.com    # Database host
DB_PORT=5432                                        # Database port
DB_USER=postgres_prod                              # Database user
DB_PASSWORD=<secure-password>                      # Database password
DB_NAME=bedrock_prod                               # Database name

# Connection pooling
DB_POOL_MIN_SIZE=10               # Minimum pooled connections
DB_POOL_MAX_SIZE=50               # Maximum pooled connections
DB_POOL_RECYCLE=3600              # Recycle connections after 1 hour
DB_ECHO_QUERIES=false             # Log SQL queries (debug only)

# SSL configuration
DB_SSL_MODE=require               # Require SSL: disable|allow|prefer|require
```

### Redis Cache (Optional)

```bash
# Redis configuration (optional)
REDIS_HOST=bedrock-prod-cache.xxxxx.cache.amazonaws.com
REDIS_PORT=6379
REDIS_PASSWORD=<secure-password>
REDIS_DB=0
REDIS_TTL_SECONDS=3600            # Cache TTL
REDIS_ENABLED=true                # Enable Redis caching
```

### AWS Bedrock Settings

```bash
# AWS Bedrock model configuration
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_REGION=us-east-1
BEDROCK_REQUEST_TIMEOUT=300       # Request timeout in seconds
BEDROCK_MAX_RETRIES=3             # Maximum retry attempts

# AWS credentials (optional if using IAM role)
# AWS_ACCESS_KEY_ID=<access-key>
# AWS_SECRET_ACCESS_KEY=<secret-key>
# AWS_SESSION_TOKEN=<token>       # For temporary credentials
```

### Authentication & Security

```bash
# JWT configuration
AUTH_JWT_SECRET_KEY=<secure-random-key>  # CRITICAL: Must be secure!
AUTH_JWT_ALGORITHM=HS256                 # HS256 or HS512
AUTH_JWT_EXPIRATION_HOURS=24             # Token expiration

# API key configuration
AUTH_API_KEY_PREFIX=sk_                  # Prefix for API keys in logs

# Rate limiting
AUTH_RATE_LIMIT_REQUESTS=100             # Requests per window
AUTH_RATE_LIMIT_WINDOW_SECONDS=60        # Rate limit window

# CORS (Cross-Origin Resource Sharing)
AUTH_ENABLE_CORS=false                   # Enable CORS (false for prod)
AUTH_CORS_ORIGINS=https://yourdomain.com # Comma-separated allowed origins
```

### Logging Settings

```bash
# Logging configuration
LOG_LEVEL=INFO                    # DEBUG|INFO|WARNING|ERROR|CRITICAL
LOG_FORMAT=json                   # json or text
LOG_ENABLE_REQUEST_LOGGING=true   # Log HTTP requests
LOG_ENABLE_DATABASE_LOGGING=false # Log SQL queries (debug only)
LOG_LOG_FILE=/var/log/bedrock-poc/app.log  # Optional: log file path
LOG_SENTRY_DSN=<sentry-dsn>      # Optional: Sentry error tracking
```

### Monitoring & Metrics

```bash
# Monitoring configuration
MONITOR_ENABLE_METRICS=true       # Enable Prometheus metrics
MONITOR_METRICS_PORT=9090         # Prometheus metrics port
MONITOR_ENABLE_HEALTH_CHECKS=true # Enable /health endpoints
MONITOR_HEALTH_CHECK_INTERVAL=30  # Health check interval (seconds)

# Distributed tracing (optional)
MONITOR_ENABLE_REQUEST_TRACING=true  # Enable request tracing
MONITOR_JAEGER_ENABLED=true          # Enable Jaeger tracing
MONITOR_JAEGER_HOST=localhost         # Jaeger collector host
MONITOR_JAEGER_PORT=6831              # Jaeger collector port (UDP)
```

### Feature Flags

```bash
# Feature flags
ENABLE_AUDIT_LOGGING=true         # Enable audit logging (always true in prod)
ENABLE_RATE_LIMITING=true         # Enable rate limiting
```

---

## Environment-Specific Setup

### Development Environment

```bash
# Copy template to .env
cp .env.template .env

# Edit .env with development values
ENVIRONMENT=development
DEBUG=true
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=postgres  # Simple password for local dev
REDIS_ENABLED=false   # Optional in dev
AUTH_JWT_SECRET_KEY=dev-secret-key-change-in-production

# Start application
python -m uvicorn bedrock_poc.api.main:app --reload
```

### Staging Environment

```bash
# Load staging configuration
cp .env.staging .env

# Verify staging values
echo $ENVIRONMENT  # Should output: staging
echo $DB_HOST      # Should output: staging-rds-endpoint

# All configuration should be similar to production but with debug enabled
DEBUG=true
ENVIRONMENT=staging
```

### Production Environment

```bash
# Load production configuration
cp .env.production .env

# Update with actual production values
# NEVER commit .env.production with real credentials!

# Verify production configuration
python -c "from bedrock_poc.config import get_settings; s = get_settings(); print(f'Environment: {s.environment}')"

# Start with systemd
systemctl start bedrock-poc
```

---

## Database Configuration

### PostgreSQL Setup (AWS RDS)

#### Step 1: Create RDS Instance

```bash
# Using AWS CLI
aws rds create-db-instance \
  --db-instance-identifier bedrock-prod \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 14.10 \
  --master-username postgres_prod \
  --master-user-password $(python -c "import secrets; print(secrets.token_urlsafe(32))") \
  --allocated-storage 100 \
  --storage-type gp3 \
  --storage-encrypted \
  --publicly-accessible false \
  --db-name bedrock_prod \
  --vpc-security-group-ids sg-xxxxx
```

#### Step 2: Configure Connection Pooling

```python
# bedrock_poc/config/settings.py already handles pooling:

DatabaseSettings:
  pool_size = 10        # Min connections
  max_overflow = 40     # Max additional connections
  pool_recycle = 3600   # Recycle after 1 hour
  pool_pre_ping = True  # Verify connection health
```

#### Step 3: Database Initialization

```bash
# Initialize database tables
python -c "from bedrock_poc.database import init_db; init_db()"

# Or with specific database URL
DATABASE_URL="postgresql://user:pass@host/db" python -c "from bedrock_poc.database import init_db; init_db()"
```

#### Step 4: Verify Connection

```bash
# Test connection
python -c "from bedrock_poc.config.database import DatabaseManager; print('OK' if DatabaseManager.health_check() else 'FAILED')"
```

### Connection String Format

```
postgresql://user:password@host:5432/database?sslmode=require
postgresql+psycopg2://user:password@host:5432/database?sslmode=require
```

---

## Security Configuration

### JWT Secret Key Generation

```bash
# Generate a secure JWT secret key (256 bits = 32 bytes)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Output example:
# G7x9kL2mN5pQ8wR3sT6uV1yZ4aB7cD0eF3gH6jK9lM2nO5p

# Set in environment
export AUTH_JWT_SECRET_KEY="G7x9kL2mN5pQ8wR3sT6uV1yZ4aB7cD0eF3gH6jK9lM2nO5p"
```

### Database Password Security

```bash
# Generate a secure database password (32 bytes)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Store in:
# 1. AWS Secrets Manager (recommended)
# 2. Kubernetes Secrets (if using K8s)
# 3. .env file (only locally, never commit)
```

### CORS Configuration

```bash
# Production: Specific trusted origins only
AUTH_ENABLE_CORS=false
AUTH_CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Development: Allow localhost
AUTH_ENABLE_CORS=true
AUTH_CORS_ORIGINS=http://localhost:3000,http://localhost:8501
```

### HTTPS/TLS Configuration

```bash
# Use reverse proxy (Nginx/HAProxy) for TLS termination
# The application listens on HTTP 8000 behind the proxy

# Example Nginx configuration:
upstream bedrock_api {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    location /api {
        proxy_pass http://bedrock_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Monitoring & Logging Setup

### Prometheus Metrics

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'bedrock-poc'
    static_configs:
      - targets: ['localhost:9090']
```

### ELK Stack Setup

```bash
# Docker Compose for ELK stack
docker-compose up -d elasticsearch logstash kibana

# Configure application to send logs to Logstash
LOG_FORMAT=json
LOG_SENTRY_DSN=<optional>
```

### CloudWatch Logging

```python
# Application automatically sends logs to CloudWatch if running on EC2/ECS
# Ensure IAM role has CloudWatch Logs permissions

# View logs
aws logs tail /aws/bedrock-poc/application --follow
```

---

## AWS Secrets Manager Integration

### Store Secrets

```bash
# Store database password
aws secretsmanager create-secret \
  --name bedrock/prod/db-password \
  --secret-string "your-secure-password"

# Store JWT secret
aws secretsmanager create-secret \
  --name bedrock/prod/jwt-secret \
  --secret-string "your-jwt-secret"

# Store API keys
aws secretsmanager create-secret \
  --name bedrock/prod/api-keys \
  --secret-string '{"key1": "value1", "key2": "value2"}'
```

### Retrieve Secrets

```python
# In your application code
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

# Usage
db_password = get_secret('bedrock/prod/db-password')
jwt_secret = get_secret('bedrock/prod/jwt-secret')
```

---

## Validation & Health Checks

### Configuration Validation

```bash
# Validate configuration at startup
python -c "from bedrock_poc.config import get_settings; s = get_settings(); print('Configuration valid')"
```

### Health Check Endpoints

```bash
# Application health
curl http://localhost:8000/api/health

# Database health
curl http://localhost:8000/api/health/db

# Detailed health
curl http://localhost:8000/api/health/detail

# Prometheus metrics
curl http://localhost:9090/metrics
```

---

## Troubleshooting

### Configuration Not Loaded

```bash
# Check environment variable
echo $DB_HOST

# Check .env file exists
ls -la .env

# Verify configuration is readable
python -c "from bedrock_poc.config import get_settings; print(get_settings().database.host)"
```

### Database Connection Failed

```bash
# Test PostgreSQL connectivity
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1"

# Check connection string
python -c "from bedrock_poc.config import get_settings; print(get_settings().database.sync_url)"

# Verify firewall rules
telnet $DB_HOST 5432
```

### JWT Secret Key Too Weak

```bash
# Error: JWT_SECRET_KEY must be at least 32 characters

# Fix: Generate a secure key
export AUTH_JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### Performance Issues

```bash
# Check database connection pool
python -c "from bedrock_poc.config import get_settings; s = get_settings(); print(f'Pool: {s.database.pool_min_size}-{s.database.pool_max_size}')"

# Increase pool size
DB_POOL_MAX_SIZE=100

# Enable query logging to identify slow queries
DB_ECHO_QUERIES=true
```

---

## Checklist for Production Deployment

- [ ] ENVIRONMENT set to `production`
- [ ] DEBUG set to `false`
- [ ] AUTH_JWT_SECRET_KEY is a secure random value (at least 32 bytes)
- [ ] DB_HOST points to production RDS instance
- [ ] DB_PASSWORD is stored in Secrets Manager or .env.local (not committed)
- [ ] DB_SSL_MODE set to `require`
- [ ] LOG_FORMAT set to `json`
- [ ] MONITOR_ENABLE_METRICS set to `true`
- [ ] ENABLE_AUDIT_LOGGING set to `true`
- [ ] ENABLE_RATE_LIMITING set to `true`
- [ ] CORS_ORIGINS set to specific trusted origins
- [ ] Database backups configured
- [ ] Monitoring and alerting configured
- [ ] Log aggregation setup (ELK/CloudWatch)
- [ ] Health check endpoints verified
- [ ] Load test completed and passed
- [ ] Security audit completed and passed

---

## Support

For issues or questions:
- Check logs: `journalctl -u bedrock-poc -f`
- Review this guide
- Contact: bsrikanthr1@gmail.com

---

**Document Status:** ✅ Complete  
**Last Review:** 2026-08-20  
**Next Review:** 2026-09-20

