# Security Architecture - Bedrock POC

## Overview

The Bedrock POC implements a comprehensive security architecture with JWT-based authentication, Role-Based Access Control (RBAC), and audit logging for compliance and traceability.

## Table of Contents

1. [Authentication](#authentication)
2. [Authorization & RBAC](#authorization--rbac)
3. [User Roles](#user-roles)
4. [Permissions](#permissions)
5. [API Endpoints Security](#api-endpoints-security)
6. [Audit Logging](#audit-logging)
7. [Best Practices](#best-practices)

## Authentication

### JWT Tokens

The system uses JSON Web Tokens (JWT) for stateless authentication:

- **Access Token**: Short-lived token (60 minutes) used for API requests
- **Refresh Token**: Long-lived token (7 days) used to obtain new access tokens

### Token Structure

Access tokens contain:
- `user_id`: User identifier
- `email`: User email address
- `role`: User role (admin, recruiter, candidate)
- `exp`: Token expiration time
- `iat`: Token issued at time
- `type`: Token type (access/refresh)

### Authentication Flow

1. User registers or logs in with email/password
2. Server validates credentials
3. Server generates JWT tokens (access + refresh)
4. Client stores tokens locally
5. Client includes access token in Authorization header for API requests
6. Server validates token on each request
7. When access token expires, client uses refresh token to obtain new access token

### Password Security

- Passwords are hashed using **Argon2** algorithm
- Minimum 8 characters required
- Passwords are never returned in responses
- Password changes require current password verification

## Authorization & RBAC

The system implements Role-Based Access Control (RBAC) to control which users can access which resources and perform which actions.

### RBAC Components

1. **Roles**: User classifications (admin, recruiter, candidate)
2. **Permissions**: Fine-grained access controls
3. **Role-Permission Mapping**: Defines which permissions each role has

### Dependency Injection

Authorization is enforced through FastAPI dependency injection:

```python
from bedrock_poc.auth import require_role, require_permission, UserRole, Permission

@app.get("/admin-only")
def admin_endpoint(current_user: User = Depends(require_role(UserRole.ADMIN))):
    return {"message": "Admin only"}

@app.post("/create-job")
def create_job(current_user: User = Depends(require_permission(Permission.CREATE_JOB))):
    return {"message": "Job created"}
```

## User Roles

### Admin Role

- **Description**: System administrators with full access
- **Responsibilities**:
  - Manage users (create, read, update, delete)
  - Manage system configuration
  - View audit logs
  - Override any permission checks
- **Capabilities**: All permissions

### Recruiter Role

- **Description**: Recruitment team members
- **Responsibilities**:
  - Create and manage job postings
  - Search and view candidate profiles
  - Create and manage candidate matches
  - View audit logs
  - Update their own profile
- **Capabilities**:
  - Job management (create, read, update, delete)
  - Candidate search and profile viewing
  - Match creation and management
  - Audit log viewing

### Candidate Role

- **Description**: Job candidates/applicants
- **Responsibilities**:
  - View and update their own profile
  - View matches related to them
  - Apply for jobs
- **Capabilities**:
  - Read own user profile
  - Update own profile
  - View matches
  - Limited audit log access for own activities

## Permissions

### Permission Categories

#### User Management
- `create_user`: Create new user accounts
- `read_user`: Read user profiles
- `update_user`: Update user information
- `delete_user`: Delete user accounts
- `manage_users`: Full user management

#### Job Management
- `create_job`: Create job postings
- `read_job`: View job details
- `update_job`: Modify job postings
- `delete_job`: Remove job postings
- `manage_jobs`: Full job management

#### Candidate Management
- `create_candidate`: Register candidates
- `read_candidate`: View candidate profiles
- `update_candidate`: Update candidate information
- `delete_candidate`: Remove candidate records
- `manage_candidates`: Full candidate management

#### Match Management
- `create_match`: Create candidate-job matches
- `read_match`: View match details
- `update_match`: Modify match status
- `delete_match`: Remove matches
- `manage_matches`: Full match management

#### System Permissions
- `view_audit_logs`: Access audit logging system
- `manage_system`: Full system administration

### Permission Reference

See [RBAC Permissions Matrix](#rbac-permissions-matrix) below for complete mapping.

## RBAC Permissions Matrix

| Permission | Admin | Recruiter | Candidate |
|-----------|-------|-----------|-----------|
| create_user | ✓ | ✗ | ✗ |
| read_user | ✓ | ✓ | ✓ |
| update_user | ✓ | ✓ | ✓ |
| delete_user | ✓ | ✗ | ✗ |
| manage_users | ✓ | ✗ | ✗ |
| create_job | ✓ | ✓ | ✗ |
| read_job | ✓ | ✓ | ✗ |
| update_job | ✓ | ✓ | ✗ |
| delete_job | ✓ | ✓ | ✗ |
| manage_jobs | ✓ | ✓ | ✗ |
| create_candidate | ✓ | ✓ | ✗ |
| read_candidate | ✓ | ✓ | ✓ |
| update_candidate | ✓ | ✓ | ✓ |
| delete_candidate | ✓ | ✗ | ✗ |
| manage_candidates | ✓ | ✓ | ✗ |
| create_match | ✓ | ✓ | ✗ |
| read_match | ✓ | ✓ | ✓ |
| update_match | ✓ | ✓ | ✗ |
| delete_match | ✓ | ✓ | ✗ |
| manage_matches | ✓ | ✓ | ✗ |
| view_audit_logs | ✓ | ✓ | ✗ |
| manage_system | ✓ | ✗ | ✗ |

## API Endpoints Security

### Protected Endpoints

All endpoints except `/api/auth/register` and `/api/auth/login` require authentication.

#### Authentication Endpoints (`/api/auth`)
- `POST /api/auth/register` - Public (create account)
- `POST /api/auth/login` - Public (obtain tokens)
- `POST /api/auth/refresh` - Authenticated (refresh access token)
- `GET /api/auth/me` - Authenticated (get current user)
- `POST /api/auth/verify-token` - Authenticated (verify token validity)
- `GET /api/auth/users` - Admin only (list all users)
- `GET /api/auth/users/{user_id}` - Authenticated (get user, admins can view any)

#### Jobs Endpoints (`/api/jobs`)
- `POST /api/jobs/parse` - Recruiter+ only (parse job description)

#### Candidates Endpoints (`/api/candidates`)
- `GET /api/candidates/` - Recruiter+ only (search candidates)
- `POST /api/candidates/search` - Recruiter+ only (advanced search)
- `GET /api/candidates/{candidate_id}` - Recruiter+ only (view candidate)

#### Matches Endpoints (`/api/matches`)
- `POST /api/matches/` - Recruiter+ only (create match)
- `GET /api/matches/{match_id}` - Recruiter+ only (view match)
- `DELETE /api/matches/{match_id}` - Recruiter+ only (delete match)
- `GET /api/matches/` - Recruiter+ only (list matches)
- `POST /api/matches/{job_id}/rank` - Recruiter+ only (rank matches)

#### Audit Endpoints (`/api/audit`)
- `GET /api/audit/logs` - Admin only (retrieve all logs)
- `GET /api/audit/logs/user/{user_id}` - Admin only (get user's logs)
- `GET /api/audit/logs/event/{event_type}` - Admin only (filter by event type)
- `GET /api/audit/logs/count` - Admin only (get log count)

## Audit Logging

Comprehensive audit logging tracks all user activities for compliance and security:

### Logged Events

#### Authentication Events
- `login`: Successful user login
- `logout`: User logout
- `login_failed`: Failed login attempt
- `token_refresh`: Token refresh operation
- `token_invalid`: Invalid token access

#### User Management Events
- `user_created`: New user registered
- `user_updated`: User information modified
- `user_deleted`: User account deleted
- `user_role_changed`: User role changed
- `user_deactivated`: User account deactivated

#### Authorization Events
- `authorization_failed`: Failed authorization check
- `permission_denied`: Permission denied for action

#### Data Modification Events
- `data_created`: New record created
- `data_updated`: Record modified
- `data_deleted`: Record deleted

#### API Access Events
- `api_access`: API endpoint accessed
- `api_error`: API error occurred

#### System Events
- `system_error`: System error occurred
- `system_config_changed`: System configuration changed

### Audit Log Fields

Each audit log entry contains:
- `id`: Log entry ID
- `event_type`: Type of event
- `user_id`: User who performed action
- `user_email`: Email of user
- `timestamp`: When event occurred
- `ip_address`: Client IP address
- `endpoint`: API endpoint accessed
- `method`: HTTP method (GET, POST, etc.)
- `resource_type`: Type of resource affected
- `resource_id`: ID of resource
- `action`: Action performed
- `status`: Success or failure
- `status_code`: HTTP status code
- `error_message`: Error details if applicable
- `changes`: Data changes made
- `metadata`: Additional context

### Audit Log Queries

Logs can be queried with filters:

```python
from bedrock_poc.audit import AuditLogger, AuditEventType

# Get all logs
logs = AuditLogger.get_logs()

# Get logs for specific user
logs = AuditLogger.get_logs_for_user(user_id=1)

# Get logs by event type
logs = AuditLogger.get_logs_by_event_type(AuditEventType.LOGIN)

# Get logs with filters
logs = AuditLogger.get_logs(
    event_type=AuditEventType.DATA_CREATED,
    user_id=1,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)
```

## Best Practices

### For Users

1. **Strong Passwords**: Use long, complex passwords (minimum 8 characters)
2. **Token Management**: Keep JWT tokens secure, never share them
3. **Regular Logout**: Logout when finished with the application
4. **Activity Monitoring**: Regularly review audit logs for suspicious activity

### For Developers

1. **Principle of Least Privilege**: Grant users minimum necessary permissions
2. **Role-Based Decisions**: Use roles and permissions, not user IDs
3. **Audit Logging**: Always log sensitive operations
4. **Secure Token Storage**: Never hardcode secrets in code
5. **HTTPS Only**: Always use HTTPS in production
6. **Token Rotation**: Implement token rotation for long-lived sessions

### For Admins

1. **Regular Audits**: Review audit logs regularly for security issues
2. **User Management**: Regularly verify user roles and permissions
3. **Access Control**: Implement network-level access controls
4. **Backup**: Regular backup of audit logs
5. **Monitoring**: Setup alerts for suspicious activities

### Production Considerations

1. **Environment Variables**: Move secrets to environment variables
2. **Database**: Replace in-memory storage with PostgreSQL
3. **HTTPS**: Enable HTTPS with valid certificates
4. **Rate Limiting**: Implement rate limiting on auth endpoints
5. **WAF**: Consider Web Application Firewall
6. **Monitoring**: Implement comprehensive monitoring and alerting
7. **Log Retention**: Define audit log retention policies
8. **Encryption**: Encrypt sensitive data at rest and in transit

## Security Checklist

- [ ] Secrets moved to environment variables
- [ ] HTTPS enabled in production
- [ ] Audit logs backed up regularly
- [ ] Rate limiting configured
- [ ] Monitoring and alerting active
- [ ] Regular security audits conducted
- [ ] User roles reviewed and updated
- [ ] Permissions properly enforced
- [ ] Token expiration configured appropriately
- [ ] Database credentials secured

## Support

For security issues or questions, contact the security team.
