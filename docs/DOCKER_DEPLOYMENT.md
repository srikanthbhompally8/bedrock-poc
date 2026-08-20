# Docker Deployment Guide

**Document Version:** 1.0  
**Last Updated:** 2026-08-20  
**Status:** Phase 4 - Docker Containerization

---

## Overview

This guide covers Docker containerization and deployment of the Bedrock POC application for development, staging, and production environments.

---

## Table of Contents

1. [Docker Architecture](#docker-architecture)
2. [Quick Start](#quick-start)
3. [Development Setup](#development-setup)
4. [Staging Deployment](#staging-deployment)
5. [Production Deployment](#production-deployment)
6. [Docker Compose Reference](#docker-compose-reference)
7. [Container Management](#container-management)
8. [Troubleshooting](#troubleshooting)

---

## Docker Architecture

### Multi-Stage Build

The Dockerfile uses a multi-stage build process to minimize production image size:

```
Stage 1: Builder
├─ Base: python:3.11-slim
├─ Install build tools (gcc, libpq-dev)
├─ Create virtual environment
└─ Install all dependencies

Stage 2: Runtime
├─ Base: python:3.11-slim
├─ Copy venv from Stage 1
├─ Install runtime dependencies only
├─ Create non-root user
├─ Copy application code
└─ Result: Minimal production image (~200MB)
```

### Image Size Optimization

- **Base Image:** python:3.11-slim (≈130MB)
- **Dependencies:** Minimal runtime packages (≈40MB)
- **Application Code:** ~5MB
- **Total:** ~175MB (target: <200MB)

### Security Features

✅ Non-root user (bedrock:bedrock)  
✅ Read-only filesystem where possible  
✅ Minimal attack surface (slim base image)  
✅ Regular security scanning  
✅ No hardcoded secrets  

---

## Quick Start

### Development Environment (Local)

```bash
# Clone repository
git clone https://github.com/srikanthbhompally8/bedrock-poc.git
cd bedrock-poc

# Build and run
docker-compose up -d

# Initialize database
docker-compose exec api python -c "from bedrock_poc.database import init_db; init_db()"

# View logs
docker-compose logs -f api

# Access API
curl http://localhost:8000/api/health
```

### Staging Environment

```bash
# Copy environment file
cp .env.staging .env.staging.local
# Edit with staging values
nano .env.staging.local

# Deploy
docker-compose -f docker-compose.staging.yml --env-file .env.staging.local up -d

# View logs
docker-compose -f docker-compose.staging.yml logs -f api
```

### Production Deployment

```bash
# Copy environment file (never commit production secrets!)
cp .env.production .env.production.local
# Edit with production values (use AWS Secrets Manager for secrets)
nano .env.production.local

# Deploy
docker-compose -f docker-compose.production.yml --env-file .env.production.local up -d

# Verify
docker-compose -f docker-compose.production.yml ps
```

---

## Development Setup

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

### Installation

```bash
# Verify Docker installation
docker --version
docker-compose --version

# If not installed, follow: https://docs.docker.com/get-docker/
```

### Configuration

The development setup includes:
- **API:** Bedrock POC application with auto-reload
- **PostgreSQL:** Local database
- **Redis:** Cache (optional, disabled by default)
- **Nginx:** Reverse proxy (optional)

### Start Development Environment

```bash
# Start all services
docker-compose up -d

# Watch logs
docker-compose logs -f

# Stop services
docker-compose down

# Remove volumes (delete data)
docker-compose down -v
```

### Development Commands

```bash
# Run tests
docker-compose exec api pytest tests/ -v

# Shell access
docker-compose exec api bash

# View logs
docker-compose logs api
docker-compose logs postgres

# Restart service
docker-compose restart api

# Rebuild image
docker-compose build --no-cache api

# Health check
curl http://localhost:8000/api/health
curl http://localhost:8000/metrics
```

### Enable Optional Services

```bash
# Start with Redis cache
docker-compose --profile cache up -d

# Start with Nginx
docker-compose --profile nginx up -d

# Start with both
docker-compose --profile cache --profile nginx up -d
```

---

## Staging Deployment

### Setup Steps

1. **Prepare Environment**

```bash
cp .env.staging .env.staging.local
# Edit with staging credentials
```

2. **Deploy Stack**

```bash
docker-compose -f docker-compose.staging.yml \
  --env-file .env.staging.local \
  up -d
```

3. **Initialize Database**

```bash
docker-compose -f docker-compose.staging.yml \
  exec api python -c "from bedrock_poc.database import init_db; init_db()"
```

4. **Verify Deployment**

```bash
# Check services
docker-compose -f docker-compose.staging.yml ps

# Check API health
curl http://localhost:8000/api/health

# Check metrics
curl http://localhost:9091/metrics
```

### Staging Services

| Service | Purpose | Port |
|---------|---------|------|
| api | Bedrock POC API | 8000 |
| postgres | PostgreSQL database | 5432 |
| redis | Cache | 6379 |
| nginx | Reverse proxy | 80/443 |
| prometheus | Metrics collection | 9091 |
| grafana | Metrics visualization | 3000 |

### Monitoring Staging

```bash
# View metrics (Prometheus)
http://localhost:9091

# View dashboards (Grafana)
http://localhost:3000
# Login: admin / ${GRAFANA_PASSWORD}
```

---

## Production Deployment

### Prerequisites

- AWS EC2 instance (t3.large or larger)
- AWS RDS PostgreSQL instance
- AWS ElastiCache Redis cluster
- IAM role with necessary permissions
- SSL/TLS certificates (Let's Encrypt)
- Domain name

### AWS Infrastructure Setup

```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier bedrock-prod \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 14.10 \
  --allocated-storage 100 \
  --storage-encrypted

# Create ElastiCache Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id bedrock-prod \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0

# Create security groups
# Ensure EC2 → RDS and EC2 → Redis connectivity
```

### EC2 Instance Setup

```bash
# SSH into EC2 instance
ssh -i your-key.pem ec2-user@your-instance.com

# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo usermod -a -G docker ec2-user
sudo systemctl start docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Deploy Application

```bash
# Clone repository
git clone https://github.com/srikanthbhompally8/bedrock-poc.git
cd bedrock-poc

# Copy production environment
cp .env.production .env.prod.local

# Edit with production credentials (use AWS Secrets Manager)
nano .env.prod.local

# Deploy
docker-compose -f docker-compose.production.yml \
  --env-file .env.prod.local \
  up -d

# Verify
docker-compose -f docker-compose.production.yml ps
```

### SSL/TLS Setup

```bash
# Install certbot
sudo yum install certbot -y

# Generate certificate (Let's Encrypt)
sudo certbot certonly --standalone \
  -d api.yourdomain.com \
  -d yourdomain.com

# Update Nginx configuration
# Copy certificates to /etc/letsencrypt (already configured in docker-compose.yml)

# Restart Nginx
docker-compose -f docker-compose.production.yml restart nginx
```

### Production Verification

```bash
# Check services
docker-compose -f docker-compose.production.yml ps

# Health check
curl https://api.yourdomain.com/api/health

# Metrics
curl http://localhost:9090/metrics

# Logs
docker-compose -f docker-compose.production.yml logs -f api
```

---

## Docker Compose Reference

### Development

```yaml
Services:
  - postgres:    PostgreSQL 14
  - redis:       Redis 7 (optional)
  - api:         Bedrock POC API (with reload)
  - nginx:       Nginx reverse proxy (optional)

Ports:
  - 5432:        PostgreSQL
  - 6379:        Redis
  - 8000:        API
  - 80:          Nginx
```

### Staging

```yaml
Services:
  - postgres:    PostgreSQL 14
  - redis:       Redis 7 with password
  - api:         Bedrock POC API (3x replicas)
  - nginx:       Nginx reverse proxy
  - prometheus:  Metrics collection
  - grafana:     Metrics visualization

Ports:
  - 8000:        API
  - 80/443:      Nginx
  - 9091:        Prometheus
  - 3000:        Grafana
```

### Production

```yaml
Services:
  - api:         Bedrock POC API (3x replicas, AWS RDS/ElastiCache)
  - nginx:       Nginx reverse proxy with SSL
  - prometheus:  Metrics collection (optional)
  - grafana:     Metrics visualization (optional)

Ports:
  - 8000:        API (behind Nginx)
  - 80/443:      Nginx
  - 9090:        Metrics (internal)
  - 3000:        Grafana (optional)
```

---

## Container Management

### Building Images

```bash
# Build development image
docker build -t bedrock-poc:dev .

# Build with specific tag
docker build -t bedrock-poc:1.0 .

# Build without cache
docker build --no-cache -t bedrock-poc:latest .
```

### Container Lifecycle

```bash
# Start containers
docker-compose up -d

# Stop containers
docker-compose stop

# Restart containers
docker-compose restart

# Remove containers
docker-compose down

# Remove volumes (delete data!)
docker-compose down -v

# View logs
docker-compose logs -f api

# Execute command
docker-compose exec api bash

# Check container status
docker-compose ps
```

### Scaling

```bash
# Scale API service (development)
docker-compose up -d --scale api=3

# Scale API service (production)
docker-compose -f docker-compose.production.yml up -d --scale api=5
```

### Security Scanning

```bash
# Scan image for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image bedrock-poc:latest

# Scan image with high severity
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image --severity HIGH bedrock-poc:latest
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Validate configuration
docker-compose config

# Rebuild image
docker-compose build --no-cache api

# Start with verbose output
docker-compose --verbose up
```

### Database Connection Failed

```bash
# Check database connectivity
docker-compose exec api nc -zv postgres 5432

# Check environment variables
docker-compose exec api env | grep DB_

# Verify database exists
docker-compose exec postgres psql -U postgres -l
```

### Metrics Not Appearing

```bash
# Check Prometheus targets
curl http://localhost:9091/api/v1/targets

# Check API metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus config
docker-compose logs prometheus
```

### Health Check Failing

```bash
# Check health endpoint
curl -v http://localhost:8000/api/health

# View detailed health
curl http://localhost:8000/api/health/detail

# Check logs
docker-compose logs api

# Restart container
docker-compose restart api
```

### Memory/CPU Issues

```bash
# Monitor resource usage
docker stats

# Increase limits
docker-compose -f docker-compose.production.yml up -d
# Edit deploy.resources.limits in docker-compose.production.yml

# Check container limits
docker inspect bedrock-api-prod | grep -A 10 "Memory"
```

---

## Best Practices

### Development

✅ Use auto-reload (`RELOAD=true`)  
✅ Keep containers running for fast iteration  
✅ Use profiles for optional services  
✅ Mount source code for live changes  

### Staging

✅ Mirror production environment  
✅ Use realistic data volumes  
✅ Enable monitoring and logging  
✅ Test deployment procedures  

### Production

✅ Use read-only root filesystem where possible  
✅ Implement health checks  
✅ Use resource limits  
✅ Enable monitoring and alerting  
✅ Automate deployments  
✅ Use secret management  
✅ Regular security scanning  

---

## Support

For issues or questions:
- Check logs: `docker-compose logs -f api`
- Review troubleshooting section
- Contact: bsrikanthr1@gmail.com

---

**Document Status:** ✅ Complete  
**Last Review:** 2026-08-20  
**Next Review:** 2026-09-20

