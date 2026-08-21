# Monitoring, Logging, and Alerting Guide

**Document Version:** 1.0  
**Last Updated:** 2026-08-20  
**Status:** Phase 4 Task 4.3 - Centralized Logging & Monitoring

---

## Overview

This guide covers centralized logging, monitoring, health checks, and alerting for the Bedrock POC application in production environments.

---

## Table of Contents

1. [Structured Logging](#structured-logging)
2. [Correlation IDs & Request Tracing](#correlation-ids--request-tracing)
3. [Prometheus Metrics](#prometheus-metrics)
4. [Health Check Endpoints](#health-check-endpoints)
5. [CloudWatch Integration](#cloudwatch-integration)
6. [Alerting Rules](#alerting-rules)
7. [Operational Dashboards](#operational-dashboards)
8. [Troubleshooting](#troubleshooting)

---

## Structured Logging

### JSON Structured Logs

All logs are output as JSON for easy parsing and aggregation:

```json
{
  "timestamp": "2026-08-20T14:30:45.123456",
  "level": "INFO",
  "logger": "bedrock_poc.api.matches",
  "message": "Match created successfully",
  "correlation_id": "bedrock-a1b2c3d4e5f6",
  "source": "matches.py:87",
  "function": "create_match",
  "status_code": 201,
  "duration_ms": 145.23
}
```

### Log Levels

| Level | Usage | Examples |
|-------|-------|----------|
| DEBUG | Development & detailed tracing | Variable values, flow decisions |
| INFO | General application events | Requests, completions, milestones |
| WARNING | Potential issues (recoverable) | Slow queries, retries, deprecated usage |
| ERROR | Errors requiring investigation | Failed requests, exceptions |
| CRITICAL | System-critical failures | Database unavailable, out of memory |

### Log Configuration

```python
# In settings.py
LOG_LEVEL=INFO                    # Development: DEBUG, Production: INFO
LOG_FORMAT=json                   # json or text
LOG_ENABLE_REQUEST_LOGGING=true   # Log all HTTP requests
LOG_ENABLE_DATABASE_LOGGING=false # Log SQL queries (debug only)
LOG_LOG_FILE=/var/log/bedrock-poc/app.log
```

---

## Correlation IDs & Request Tracing

### Request Flow Tracking

Every request is assigned a correlation ID for end-to-end tracing:

```
Client Request
    ↓
X-Correlation-ID header extracted/generated
    ↓
Set in context variable (thread-safe)
    ↓
Added to all logs, metrics, and responses
    ↓
Passed through service calls
    ↓
Client Response includes X-Correlation-ID header
```

### Usage

```python
from bedrock_poc.logging import get_correlation_id, set_correlation_id

# Get current correlation ID (generates if not set)
correlation_id = get_correlation_id()
# Output: bedrock-a1b2c3d4e5f6

# Set correlation ID from incoming request
set_correlation_id(request.headers.get("X-Correlation-ID"))

# All subsequent logs automatically include this correlation ID
logger.info("Processing request")  # Automatically includes correlation_id
```

### Tracing Example

```bash
# Client sends request with correlation ID
curl -H "X-Correlation-ID: bedrock-user123abc" \
  http://api.example.com/api/matches

# Response includes same correlation ID
HTTP/1.1 200 OK
X-Correlation-ID: bedrock-user123abc

# All logs can be traced using this ID
grep "bedrock-user123abc" /var/log/bedrock-poc/app.log
```

---

## Prometheus Metrics

### API Metrics

Track all API endpoints with detailed metrics:

```
bedrock_api_requests_total          # Total requests by method/endpoint/status
bedrock_api_request_duration_seconds # Request duration (0.05s-10s buckets)
bedrock_api_errors_total            # Errors by method/endpoint/error_type
```

### Database Metrics

```
bedrock_database_query_duration_seconds # Query duration (0.01s-5s buckets)
bedrock_database_connections_active     # Active connection count
```

### Bedrock API Metrics

```
bedrock_bedrock_api_duration_seconds    # Bedrock API call duration
bedrock_bedrock_api_errors_total        # Bedrock API errors
bedrock_tokens_used_total               # Tokens consumed
```

### Cache Metrics

```
bedrock_cache_hits_total                # Cache hit count
bedrock_cache_misses_total              # Cache miss count
```

### Authentication Metrics

```
bedrock_auth_attempts_total             # Auth attempts by method/result
bedrock_auth_failures_total             # Auth failures by reason
```

### Business Logic Metrics

```
bedrock_job_parsing_total               # Jobs parsed by status
bedrock_matching_total                  # Matches performed by result
bedrock_ranking_duration_seconds        # Ranking operation duration
```

### Scraping Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 30s
  evaluation_interval: 30s

scrape_configs:
  - job_name: 'bedrock-api'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Viewing Metrics

```bash
# Query all metrics
curl http://localhost:9090/metrics

# Query specific metric
curl http://localhost:9090/metrics | grep bedrock_api_requests_total

# In Prometheus UI (http://localhost:9091)
# Query examples:
rate(bedrock_api_requests_total[5m])                    # Requests per second
histogram_quantile(0.95, bedrock_api_request_duration) # 95th percentile latency
bedrock_database_connections_active                    # Active connections
```

---

## Health Check Endpoints

### Liveness Check

Indicates if the application is running and responsive:

```bash
GET /api/health

Response:
{
  "status": "healthy",
  "timestamp": "2026-08-20T14:30:45.123456",
  "version": "v1"
}
```

**Purpose:** Used by load balancers to determine if container is alive  
**Frequency:** Every 30 seconds  
**Failure Action:** Restart container

### Readiness Check

Indicates if application can handle traffic (all dependencies ready):

```bash
GET /api/health/ready

Response:
{
  "status": "ready",
  "timestamp": "2026-08-20T14:30:45.123456",
  "checks": {
    "database": {
      "status": "healthy",
      "host": "bedrock-prod-rds.amazonaws.com"
    },
    "redis": {
      "status": "healthy",
      "host": "bedrock-prod-cache.amazonaws.com"
    },
    "configuration": {
      "status": "healthy",
      "environment": "production"
    }
  }
}
```

**Purpose:** Used by load balancers to route traffic  
**Frequency:** Every 30 seconds  
**Failure Action:** Stop routing traffic, but don't restart

### Detailed Health

Comprehensive health information for monitoring dashboards:

```bash
GET /api/health/detail

Response:
{
  "status": "ok",
  "timestamp": "2026-08-20T14:30:45.123456",
  "details": {
    "application": {
      "name": "Bedrock POC",
      "version": "v1",
      "environment": "production"
    },
    "configuration": {
      "database": {
        "host": "bedrock-prod-rds.amazonaws.com",
        "pool_size": 10,
        "max_connections": 50
      },
      "bedrock": {
        "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "region": "us-east-1"
      }
    },
    "dependencies": {
      "database": {
        "healthy": true,
        "timestamp": "2026-08-20T14:30:45.123456"
      },
      "redis": {
        "healthy": true,
        "timestamp": "2026-08-20T14:30:45.123456"
      }
    }
  }
}
```

---

## CloudWatch Integration

### AWS CloudWatch Logs

Application logs are automatically sent to CloudWatch in production:

```bash
# View logs
aws logs tail /aws/bedrock-poc/application --follow

# Filter by correlation ID
aws logs filter-log-events \
  --log-group-name /aws/bedrock-poc/application \
  --filter-pattern "bedrock-user123abc"

# Get log statistics
aws logs get-log-statistics \
  --log-group-name /aws/bedrock-poc/application \
  --start-time 1629456600000 \
  --end-time 1629543000000
```

### CloudWatch Metrics

Application metrics are published to CloudWatch:

```bash
# View metrics
aws cloudwatch list-metrics \
  --namespace Bedrock/POC

# Get metric statistics
aws cloudwatch get-metric-statistics \
  --namespace Bedrock/POC \
  --metric-name APIRequestDuration \
  --start-time 2026-08-20T00:00:00Z \
  --end-time 2026-08-20T23:59:59Z \
  --period 60 \
  --statistics Average,Maximum
```

### CloudWatch Alarms

Create alarms for critical metrics:

```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name bedrock-api-errors-high \
  --alarm-description "Alert when error rate > 1%" \
  --metric-name APIErrorRate \
  --namespace Bedrock/POC \
  --statistic Average \
  --period 300 \
  --threshold 1.0 \
  --comparison-operator GreaterThanThreshold

# Database connection pool exhaustion
aws cloudwatch put-metric-alarm \
  --alarm-name bedrock-db-connections-high \
  --alarm-description "Alert when connections near limit" \
  --metric-name DatabaseConnections \
  --namespace Bedrock/POC \
  --statistic Maximum \
  --period 60 \
  --threshold 40 \
  --comparison-operator GreaterThanThreshold
```

---

## Alerting Rules

### Critical Alerts (Page On-Call)

| Alert | Condition | Action |
|-------|-----------|--------|
| **Application Down** | Liveness check failing for 2 minutes | Restart service immediately |
| **Database Unavailable** | Database connection fails | Failover to read replica |
| **Error Rate High** | >5% error rate for 5 minutes | Investigate logs, check Bedrock API |
| **Response Time High** | p95 latency >2s for 10 minutes | Check database queries, scale up |
| **Authentication Failures** | >10 failures/min | Check auth service, review logs |

### Warning Alerts (Notify Team)

| Alert | Condition | Action |
|-------|-----------|--------|
| **Slow Queries** | Database query >1s | Analyze query plan, add indexes |
| **Cache Miss Rate High** | >50% miss rate | Check cache size, TTL configuration |
| **Bedrock API Slow** | >5s response time | Check rate limits, Bedrock capacity |
| **Memory Usage High** | >80% of limit | Monitor for leaks, scale up |
| **Disk Usage High** | >80% utilization | Check log rotation, cleanup |

### Alert Templates

```yaml
# prometheus/alert_rules.yml
groups:
  - name: bedrock_alerts
    rules:
      # Critical: High error rate
      - alert: HighErrorRate
        expr: |
          (rate(bedrock_api_errors_total[5m]) / rate(bedrock_api_requests_total[5m])) > 0.05
        for: 5m
        annotations:
          summary: "High API error rate (>5%)"
          description: "Error rate is {{ $value | humanizePercentage }}"
          severity: critical

      # Warning: High latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, bedrock_api_request_duration_seconds) > 2
        for: 10m
        annotations:
          summary: "High API latency (>2s)"
          description: "P95 latency is {{ $value }}s"
          severity: warning

      # Critical: Database unavailable
      - alert: DatabaseUnavailable
        expr: bedrock_database_connections_active == 0
        for: 1m
        annotations:
          summary: "Database connection lost"
          severity: critical

      # Warning: Connection pool near limit
      - alert: ConnectionPoolNearLimit
        expr: |
          bedrock_database_connections_active / 50 > 0.8
        for: 5m
        annotations:
          summary: "Database connection pool near limit"
          description: "Using {{ $value | humanizePercentage }} of available connections"
          severity: warning
```

---

## Operational Dashboards

### Grafana Dashboard

Create dashboards to visualize key metrics:

```json
{
  "dashboard": {
    "title": "Bedrock POC - Production Monitoring",
    "panels": [
      {
        "title": "API Request Rate",
        "targets": [
          {
            "expr": "rate(bedrock_api_requests_total[5m])"
          }
        ]
      },
      {
        "title": "API Latency (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, bedrock_api_request_duration_seconds)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(bedrock_api_errors_total[5m])"
          }
        ]
      },
      {
        "title": "Database Connections",
        "targets": [
          {
            "expr": "bedrock_database_connections_active"
          }
        ]
      },
      {
        "title": "Bedrock API Latency",
        "targets": [
          {
            "expr": "rate(bedrock_bedrock_api_duration_seconds[5m])"
          }
        ]
      },
      {
        "title": "Token Usage",
        "targets": [
          {
            "expr": "rate(bedrock_tokens_used_total[1h])"
          }
        ]
      }
    ]
  }
}
```

### Key Metrics to Monitor

```
1. API Metrics
   - Requests per second
   - Latency (p50, p95, p99)
   - Error rate by endpoint
   - HTTP status code distribution

2. Database Metrics
   - Query duration
   - Active connections
   - Connection pool utilization
   - Query errors

3. Bedrock API Metrics
   - Call duration
   - Error rate
   - Tokens consumed per hour
   - Rate limit status

4. System Metrics
   - CPU usage
   - Memory usage
   - Disk usage
   - Network I/O

5. Business Metrics
   - Jobs parsed per hour
   - Matches created per hour
   - Average ranking duration
   - Cache hit rate
```

---

## Troubleshooting

### Logs Not Appearing

```bash
# Check logging is enabled
curl http://localhost:8000/api/health/detail | grep request_logging

# Verify log file permissions
ls -la /var/log/bedrock-poc/app.log

# Check log format
tail /var/log/bedrock-poc/app.log | head -1 | python -m json.tool

# Increase log level for debugging
LOG_LEVEL=DEBUG docker-compose restart api
```

### Metrics Not Collecting

```bash
# Check metrics endpoint
curl http://localhost:9090/metrics

# Verify Prometheus scrape config
curl http://localhost:9091/api/v1/targets

# Check if Prometheus is scraping
curl http://localhost:9091/api/v1/query?query=bedrock_api_requests_total
```

### Health Checks Failing

```bash
# Test liveness
curl http://localhost:8000/api/health

# Test readiness
curl http://localhost:8000/api/health/ready

# Get detailed info
curl http://localhost:8000/api/health/detail | python -m json.tool

# Test specific dependencies
# Database
docker-compose exec api nc -zv postgres 5432

# Redis
docker-compose exec api redis-cli -h redis ping
```

### High Latency

```bash
# Check database queries
tail -f /var/log/bedrock-poc/app.log | grep "database_query_duration"

# Check Bedrock API calls
tail -f /var/log/bedrock-poc/app.log | grep "bedrock_duration"

# View latency percentiles in Prometheus
histogram_quantile(0.50, bedrock_api_request_duration_seconds)
histogram_quantile(0.95, bedrock_api_request_duration_seconds)
histogram_quantile(0.99, bedrock_api_request_duration_seconds)
```

---

## Best Practices

✅ **Logging**
- Use JSON format for production
- Include correlation IDs
- Log at appropriate levels
- Rotate logs regularly
- Archive old logs

✅ **Metrics**
- Scrape every 30 seconds
- Keep metrics for 30+ days
- Use appropriate buckets
- Label metrics consistently
- Alert on key thresholds

✅ **Health Checks**
- Liveness: fast, only checks if running
- Readiness: thorough, checks dependencies
- 30-second intervals recommended
- Handle graceful shutdown

✅ **Alerting**
- Alert on symptoms, not noise
- Set thresholds based on SLA
- Include context in alert messages
- Have runbooks for each alert
- Test alert paths regularly

---

## Support

For monitoring issues:
- Check logs: `docker-compose logs api`
- Review metrics: http://localhost:9091
- Check health: http://localhost:8000/api/health/detail
- Contact: bsrikanthr1@gmail.com

---

**Document Status:** ✅ Complete  
**Last Review:** 2026-08-20  
**Next Review:** 2026-09-20

