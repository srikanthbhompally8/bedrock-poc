"""Audit logging models for tracking system events."""

from enum import Enum
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class AuditEventType(str, Enum):
    """Types of audit events to log."""

    # Authentication events
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_INVALID = "token_invalid"

    # User management events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ROLE_CHANGED = "user_role_changed"
    USER_DEACTIVATED = "user_deactivated"

    # Authorization events
    AUTHORIZATION_FAILED = "authorization_failed"
    PERMISSION_DENIED = "permission_denied"

    # Data modification events
    DATA_CREATED = "data_created"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"

    # API access events
    API_ACCESS = "api_access"
    API_ERROR = "api_error"

    # System events
    SYSTEM_ERROR = "system_error"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"


class AuditLogEntry(BaseModel):
    """Individual audit log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    event_type: AuditEventType
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    status: str = "success"
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "timestamp": self.timestamp,
            "ip_address": self.ip_address,
            "endpoint": self.endpoint,
            "method": self.method,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "status": self.status,
            "status_code": self.status_code,
            "error_message": self.error_message,
            "changes": self.changes,
            "metadata": self.metadata,
        }


class AuditLog(BaseModel):
    """Query response for audit logs."""

    model_config = ConfigDict(from_attributes=True)

    total: int = 0
    entries: list[AuditLogEntry] = []
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    filters: Optional[Dict[str, Any]] = None
