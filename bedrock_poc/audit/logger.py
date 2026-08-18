"""Audit logging service for tracking system events."""

from datetime import datetime
from typing import Optional, Any, Dict, List
from bedrock_poc.audit.models import AuditEventType, AuditLogEntry, AuditLog

# In-memory audit log storage (replace with database in production)
audit_logs: Dict[int, Dict[str, Any]] = {}
next_log_id = 1


class AuditLogger:
    """Service for audit logging operations."""

    @staticmethod
    def log_event(
        event_type: AuditEventType,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        status: str = "success",
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLogEntry:
        """Log an audit event.

        Args:
            event_type: Type of event to log
            user_id: User ID associated with event
            user_email: User email associated with event
            ip_address: Client IP address
            endpoint: API endpoint accessed
            method: HTTP method used
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            action: Action performed
            status: Event status (success/failure)
            status_code: HTTP status code
            error_message: Error message if applicable
            changes: Data changes made
            metadata: Additional metadata

        Returns:
            Created AuditLogEntry
        """
        global next_log_id

        entry = AuditLogEntry(
            id=next_log_id,
            event_type=event_type,
            user_id=user_id,
            user_email=user_email,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            endpoint=endpoint,
            method=method,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            status=status,
            status_code=status_code,
            error_message=error_message,
            changes=changes,
            metadata=metadata,
        )

        # Store in memory
        audit_logs[next_log_id] = entry.to_dict()
        next_log_id += 1

        return entry

    @staticmethod
    def log_authentication(
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        event_type: AuditEventType = AuditEventType.LOGIN,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> AuditLogEntry:
        """Log authentication event.

        Args:
            user_id: User ID
            user_email: User email
            ip_address: Client IP
            event_type: Type of auth event
            status: Event status
            error_message: Error message if failed

        Returns:
            Created AuditLogEntry
        """
        return AuditLogger.log_event(
            event_type=event_type,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            endpoint="/api/auth/login",
            method="POST",
            status=status,
            error_message=error_message,
        )

    @staticmethod
    def log_authorization_failure(
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        required_permission: Optional[str] = None,
    ) -> AuditLogEntry:
        """Log authorization failure.

        Args:
            user_id: User ID
            user_email: User email
            ip_address: Client IP
            endpoint: Endpoint accessed
            method: HTTP method
            required_permission: Permission required

        Returns:
            Created AuditLogEntry
        """
        return AuditLogger.log_event(
            event_type=AuditEventType.AUTHORIZATION_FAILED,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            endpoint=endpoint,
            method=method,
            status="failure",
            error_message=f"Required permission: {required_permission}" if required_permission else "Permission denied",
        )

    @staticmethod
    def log_data_modification(
        event_type: AuditEventType,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        resource_type: str = "unknown",
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
    ) -> AuditLogEntry:
        """Log data modification event.

        Args:
            event_type: Type of modification
            user_id: User ID
            user_email: User email
            resource_type: Type of resource
            resource_id: ID of resource
            action: Action performed
            changes: Changes made

        Returns:
            Created AuditLogEntry
        """
        return AuditLogger.log_event(
            event_type=event_type,
            user_id=user_id,
            user_email=user_email,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            changes=changes,
        )

    @staticmethod
    def log_api_access(
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        status: str = "success",
    ) -> AuditLogEntry:
        """Log API access.

        Args:
            user_id: User ID
            user_email: User email
            ip_address: Client IP
            endpoint: Endpoint accessed
            method: HTTP method
            status_code: Response status code
            status: Event status

        Returns:
            Created AuditLogEntry
        """
        return AuditLogger.log_event(
            event_type=AuditEventType.API_ACCESS,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            status=status,
        )

    @staticmethod
    def get_logs(
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> AuditLog:
        """Retrieve audit logs with filtering.

        Args:
            limit: Maximum logs to return
            offset: Number of logs to skip
            event_type: Filter by event type
            user_id: Filter by user ID
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            AuditLog with matching entries
        """
        logs_list = list(audit_logs.values())

        # Apply filters
        filtered_logs = logs_list

        if event_type:
            filtered_logs = [
                log for log in filtered_logs
                if log["event_type"] == event_type.value
            ]

        if user_id:
            filtered_logs = [
                log for log in filtered_logs
                if log["user_id"] == user_id
            ]

        if start_date:
            filtered_logs = [
                log for log in filtered_logs
                if log["timestamp"] >= start_date
            ]

        if end_date:
            filtered_logs = [
                log for log in filtered_logs
                if log["timestamp"] <= end_date
            ]

        # Sort by timestamp descending
        filtered_logs.sort(key=lambda x: x["timestamp"], reverse=True)

        # Apply pagination
        total = len(filtered_logs)
        paginated = filtered_logs[offset:offset + limit]

        # Convert to AuditLogEntry objects
        entries = [
            AuditLogEntry(
                id=log.get("id"),
                event_type=AuditEventType(log["event_type"]),
                user_id=log.get("user_id"),
                user_email=log.get("user_email"),
                timestamp=log.get("timestamp"),
                ip_address=log.get("ip_address"),
                endpoint=log.get("endpoint"),
                method=log.get("method"),
                resource_type=log.get("resource_type"),
                resource_id=log.get("resource_id"),
                action=log.get("action"),
                status=log.get("status"),
                status_code=log.get("status_code"),
                error_message=log.get("error_message"),
                changes=log.get("changes"),
                metadata=log.get("metadata"),
            )
            for log in paginated
        ]

        return AuditLog(
            total=total,
            entries=entries,
            start_date=start_date,
            end_date=end_date,
            filters={
                "event_type": event_type.value if event_type else None,
                "user_id": user_id,
            },
        )

    @staticmethod
    def get_logs_for_user(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditLog:
        """Get all audit logs for a specific user.

        Args:
            user_id: User ID to filter by
            limit: Maximum logs to return
            offset: Number of logs to skip

        Returns:
            AuditLog with user's events
        """
        return AuditLogger.get_logs(
            limit=limit,
            offset=offset,
            user_id=user_id,
        )

    @staticmethod
    def get_logs_by_event_type(
        event_type: AuditEventType,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditLog:
        """Get audit logs by event type.

        Args:
            event_type: Event type to filter by
            limit: Maximum logs to return
            offset: Number of logs to skip

        Returns:
            AuditLog with matching events
        """
        return AuditLogger.get_logs(
            limit=limit,
            offset=offset,
            event_type=event_type,
        )

    @staticmethod
    def clear_logs() -> None:
        """Clear all audit logs (use with caution)."""
        global audit_logs, next_log_id
        audit_logs.clear()
        next_log_id = 1

    @staticmethod
    def get_log_count() -> int:
        """Get total number of audit logs."""
        return len(audit_logs)
