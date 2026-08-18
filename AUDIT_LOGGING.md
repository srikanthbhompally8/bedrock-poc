# Audit Logging Documentation

## Overview

The Bedrock POC audit logging system provides comprehensive logging of all user activities, authentication events, data modifications, and API access for compliance, security, and traceability purposes.

## Table of Contents

1. [Audit Log Schema](#audit-log-schema)
2. [Event Types](#event-types)
3. [API Endpoints](#api-endpoints)
4. [Usage Examples](#usage-examples)
5. [Query Patterns](#query-patterns)
6. [Compliance](#compliance)
7. [Best Practices](#best-practices)

## Audit Log Schema

Each audit log entry contains the following fields:

### Core Fields
- **id** (integer): Unique audit log entry identifier
- **event_type** (enum): Type of event that occurred
- **timestamp** (datetime): When the event occurred (UTC)
- **status** (string): Status of the event (success/failure)

### User Information
- **user_id** (integer, nullable): ID of the user who performed the action
- **user_email** (string, nullable): Email of the user

### Request Information
- **ip_address** (string, nullable): Client IP address
- **endpoint** (string, nullable): API endpoint accessed
- **method** (string, nullable): HTTP method (GET, POST, PUT, DELETE)
- **status_code** (integer, nullable): HTTP response status code

### Resource Information
- **resource_type** (string, nullable): Type of resource affected (User, Job, Candidate, Match)
- **resource_id** (string, nullable): ID of the resource
- **action** (string, nullable): Specific action performed (create, update, delete)

### Additional Information
- **error_message** (string, nullable): Error details if action failed
- **changes** (object, nullable): Data changes made (for updates)
- **metadata** (object, nullable): Additional context-specific information

### SQL Schema

```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    user_id INTEGER,
    user_email VARCHAR(255),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    endpoint VARCHAR(255),
    method VARCHAR(10),
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    action VARCHAR(50),
    status VARCHAR(20) NOT NULL,
    status_code INTEGER,
    error_message TEXT,
    changes JSONB,
    metadata JSONB,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
```

## Event Types

### Authentication Events

#### LOGIN
- **Description**: Successful user login
- **Status**: success/failure
- **Endpoint**: `/api/auth/login`
- **Example**:
```json
{
  "event_type": "login",
  "user_id": 1,
  "user_email": "user@example.com",
  "ip_address": "192.168.1.1",
  "status": "success",
  "status_code": 200
}
```

#### LOGIN_FAILED
- **Description**: Failed login attempt
- **Status**: failure
- **Endpoint**: `/api/auth/login`
- **Example**:
```json
{
  "event_type": "login_failed",
  "user_email": "user@example.com",
  "ip_address": "192.168.1.1",
  "status": "failure",
  "error_message": "Invalid password"
}
```

#### LOGOUT
- **Description**: User logout
- **Status**: success
- **Endpoint**: `/api/auth/logout`

#### TOKEN_REFRESH
- **Description**: Access token refresh
- **Status**: success/failure
- **Endpoint**: `/api/auth/refresh`

#### TOKEN_INVALID
- **Description**: Invalid token access attempt
- **Status**: failure
- **Error**: Authorization error

### User Management Events

#### USER_CREATED
- **Description**: New user registered
- **Status**: success
- **Resource Type**: User
- **Example**:
```json
{
  "event_type": "user_created",
  "user_id": 1,
  "user_email": "admin@example.com",
  "resource_type": "User",
  "resource_id": "123",
  "action": "create",
  "status": "success",
  "changes": {
    "email": "newuser@example.com",
    "full_name": "John Doe",
    "role": "candidate"
  }
}
```

#### USER_UPDATED
- **Description**: User information modified
- **Status**: success
- **Resource Type**: User

#### USER_DELETED
- **Description**: User account deleted
- **Status**: success
- **Resource Type**: User

#### USER_ROLE_CHANGED
- **Description**: User role changed
- **Status**: success
- **Example**:
```json
{
  "event_type": "user_role_changed",
  "user_id": 1,
  "resource_type": "User",
  "resource_id": "123",
  "status": "success",
  "changes": {
    "old_role": "candidate",
    "new_role": "recruiter"
  }
}
```

#### USER_DEACTIVATED
- **Description**: User account deactivated
- **Status**: success
- **Resource Type**: User

### Authorization Events

#### AUTHORIZATION_FAILED
- **Description**: Authorization check failed
- **Status**: failure
- **Example**:
```json
{
  "event_type": "authorization_failed",
  "user_id": 2,
  "user_email": "recruiter@example.com",
  "ip_address": "10.0.0.1",
  "endpoint": "/api/admin/users",
  "method": "GET",
  "status": "failure",
  "error_message": "Required permission: MANAGE_USERS"
}
```

#### PERMISSION_DENIED
- **Description**: Permission denied for specific action
- **Status**: failure

### Data Modification Events

#### DATA_CREATED
- **Description**: New record created
- **Status**: success
- **Example**:
```json
{
  "event_type": "data_created",
  "user_id": 1,
  "resource_type": "Job",
  "resource_id": "job_123",
  "action": "create",
  "status": "success",
  "changes": {
    "title": "Senior Engineer",
    "department": "Engineering"
  }
}
```

#### DATA_UPDATED
- **Description**: Record modified
- **Status**: success
- **Changes**: Shows before/after values

#### DATA_DELETED
- **Description**: Record deleted
- **Status**: success

### API Access Events

#### API_ACCESS
- **Description**: API endpoint accessed
- **Status**: success
- **Example**:
```json
{
  "event_type": "api_access",
  "user_id": 1,
  "user_email": "user@example.com",
  "ip_address": "192.168.1.1",
  "endpoint": "/api/candidates",
  "method": "GET",
  "status": "success",
  "status_code": 200
}
```

#### API_ERROR
- **Description**: API error occurred
- **Status**: failure

### System Events

#### SYSTEM_ERROR
- **Description**: System error occurred
- **Status**: failure

#### SYSTEM_CONFIG_CHANGED
- **Description**: System configuration changed
- **Status**: success
- **Resource Type**: System

## API Endpoints

All audit endpoints require `VIEW_AUDIT_LOGS` permission (Admin and Recruiter only).

### GET /api/audit/logs

Retrieve audit logs with optional filtering.

**Parameters:**
- `limit` (integer, default=100): Maximum logs to return
- `offset` (integer, default=0): Number of logs to skip
- `event_type` (string, optional): Filter by event type
- `user_id` (integer, optional): Filter by user ID

**Response:**
```json
{
  "total": 150,
  "entries": [
    {
      "id": 150,
      "event_type": "login",
      "user_id": 1,
      "user_email": "user@example.com",
      "timestamp": "2024-01-15T10:30:00Z",
      "ip_address": "192.168.1.1",
      "endpoint": "/api/auth/login",
      "method": "POST",
      "status": "success",
      "status_code": 200
    }
  ],
  "start_date": null,
  "end_date": null,
  "filters": {
    "event_type": null,
    "user_id": null
  }
}
```

### GET /api/audit/logs/user/{user_id}

Get audit logs for a specific user.

**Parameters:**
- `user_id` (integer): User ID
- `limit` (integer, default=50): Maximum logs to return
- `offset` (integer, default=0): Number of logs to skip

**Response:** AuditLog object with user's events

### GET /api/audit/logs/event/{event_type}

Get audit logs by event type.

**Parameters:**
- `event_type` (string): Event type to filter by
- `limit` (integer, default=50): Maximum logs to return
- `offset` (integer, default=0): Number of logs to skip

**Valid Event Types:**
- login, logout, login_failed, token_refresh, token_invalid
- user_created, user_updated, user_deleted, user_role_changed, user_deactivated
- authorization_failed, permission_denied
- data_created, data_updated, data_deleted
- api_access, api_error
- system_error, system_config_changed

**Response:** AuditLog object with matching events

### GET /api/audit/logs/count

Get total number of audit logs.

**Response:**
```json
{
  "total": 1250
}
```

## Usage Examples

### Python SDK

```python
from bedrock_poc.audit import AuditLogger, AuditEventType
from datetime import datetime, timedelta

# Log an event
entry = AuditLogger.log_authentication(
    user_id=1,
    user_email="user@example.com",
    ip_address="192.168.1.1",
    event_type=AuditEventType.LOGIN,
    status="success"
)

# Log a data modification
AuditLogger.log_data_modification(
    event_type=AuditEventType.DATA_CREATED,
    user_id=1,
    user_email="admin@example.com",
    resource_type="Job",
    resource_id="job_123",
    changes={"title": "Senior Engineer"}
)

# Retrieve logs
logs = AuditLogger.get_logs(limit=100)

# Get logs for specific user
user_logs = AuditLogger.get_logs_for_user(user_id=1, limit=50)

# Get logs by event type
login_logs = AuditLogger.get_logs_by_event_type(AuditEventType.LOGIN, limit=50)

# Get logs with filtering
recent_logs = AuditLogger.get_logs(
    event_type=AuditEventType.DATA_CREATED,
    user_id=1,
    start_date=datetime.utcnow() - timedelta(days=7),
    end_date=datetime.utcnow()
)

# Get total log count
count = AuditLogger.get_log_count()
```

### cURL Examples

```bash
# Get all audit logs
curl -X GET "http://localhost:8000/api/audit/logs" \
  -H "Authorization: Bearer <token>"

# Get logs for specific user
curl -X GET "http://localhost:8000/api/audit/logs/user/1" \
  -H "Authorization: Bearer <token>"

# Get logs by event type
curl -X GET "http://localhost:8000/api/audit/logs/event/login" \
  -H "Authorization: Bearer <token>"

# Get audit log count
curl -X GET "http://localhost:8000/api/audit/logs/count" \
  -H "Authorization: Bearer <token>"

# Get logs with pagination
curl -X GET "http://localhost:8000/api/audit/logs?limit=50&offset=100" \
  -H "Authorization: Bearer <token>"
```

## Query Patterns

### Common Queries

```python
# Failed logins in the last 24 hours
from datetime import datetime, timedelta

logs = AuditLogger.get_logs(
    event_type=AuditEventType.LOGIN_FAILED,
    start_date=datetime.utcnow() - timedelta(hours=24)
)

# All actions by a specific user
user_logs = AuditLogger.get_logs_for_user(user_id=5)

# Data deletions
deletion_logs = AuditLogger.get_logs(event_type=AuditEventType.DATA_DELETED)

# Authorization failures
auth_failures = AuditLogger.get_logs(
    event_type=AuditEventType.AUTHORIZATION_FAILED
)

# All events for a resource
resource_logs = AuditLogger.get_logs(
    filters={"resource_type": "Job", "resource_id": "job_123"}
)
```

## Compliance

### GDPR Compliance

- Audit logs contain personal data (user emails, IPs)
- Implement data retention policies
- Provide audit log export/deletion mechanisms
- Obtain consent for tracking

### SOC 2 Compliance

- Logs capture all user activities
- Include authentication events
- Track authorization failures
- Log data modifications
- Maintain log integrity

### HIPAA Compliance (if applicable)

- Encrypt audit logs at rest and in transit
- Implement access controls for audit logs
- Define audit log retention policies
- Log all access to sensitive data

### Best Practices

1. **Retention Policy**: Define how long to keep logs (recommend: 1-2 years)
2. **Archival**: Archive old logs to long-term storage
3. **Encryption**: Encrypt logs at rest and in transit
4. **Access Control**: Restrict audit log access to authorized users
5. **Monitoring**: Monitor for suspicious patterns
6. **Backup**: Regular backup of audit logs
7. **Integrity**: Protect logs from tampering

## Best Practices

### For Logging

1. **Log Early, Log Often**: Log important events
2. **Include Context**: Add relevant metadata
3. **Use Consistent Format**: Follow schema consistently
4. **Include Timestamps**: Use UTC timestamps
5. **Log Status**: Always include success/failure status
6. **Track Changes**: Log data before and after changes

### For Querying

1. **Use Indexes**: Index frequently queried fields
2. **Time-Based Queries**: Use timestamp ranges for efficiency
3. **Pagination**: Use limit/offset for large result sets
4. **Filtering**: Apply filters to reduce result set
5. **Archival**: Archive old logs separately

### For Analysis

1. **Regular Reviews**: Review logs regularly for anomalies
2. **Alerting**: Setup alerts for suspicious activities
3. **Trends**: Track patterns over time
4. **Reports**: Generate regular audit reports
5. **Investigations**: Use logs for security investigations

### For Production

1. **Database Storage**: Migrate from in-memory to database
2. **Log Rotation**: Implement log rotation policies
3. **Monitoring**: Setup comprehensive monitoring
4. **Alerting**: Configure alerts for critical events
5. **Archival**: Archive logs to cold storage
6. **Retention**: Define and enforce retention policies
7. **Compliance**: Ensure compliance with regulations

## Migration to Database

To migrate audit logs to PostgreSQL:

```python
# Current: In-memory storage
# Location: bedrock_poc/audit/logger.py

# Update schema
# Location: bedrock_poc/database.py

# Implement AuditService
# Location: bedrock_poc/services/audit_service.py

# Update logging calls
# Replace direct logger calls with database writes
```

## Support

For audit logging questions or issues, contact the security team.
