"""Audit logging API endpoints."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from bedrock_poc.auth import (
    User,
    UserRole,
    require_role,
    require_permission,
    Permission,
)
from bedrock_poc.audit import AuditLogger, AuditLog, AuditEventType

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/logs", response_model=AuditLog)
def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    event_type: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(require_permission(Permission.VIEW_AUDIT_LOGS)),
):
    """Get audit logs (admin only).

    Args:
        limit: Maximum logs to return
        offset: Number of logs to skip
        event_type: Filter by event type
        user_id: Filter by user ID
        current_user: Current authenticated admin user

    Returns:
        AuditLog with matching entries

    Raises:
        HTTPException: If user is not an admin
    """
    filter_event_type = None
    if event_type:
        try:
            filter_event_type = AuditEventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type: {event_type}"
            )

    return AuditLogger.get_logs(
        limit=limit,
        offset=offset,
        event_type=filter_event_type,
        user_id=user_id,
    )


@router.get("/logs/user/{user_id}", response_model=AuditLog)
def get_user_audit_logs(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_permission(Permission.VIEW_AUDIT_LOGS)),
):
    """Get audit logs for a specific user (admin only).

    Args:
        user_id: User ID to filter by
        limit: Maximum logs to return
        offset: Number of logs to skip
        current_user: Current authenticated admin user

    Returns:
        AuditLog with user's events

    Raises:
        HTTPException: If user is not an admin
    """
    return AuditLogger.get_logs_for_user(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


@router.get("/logs/event/{event_type}", response_model=AuditLog)
def get_logs_by_event_type(
    event_type: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_permission(Permission.VIEW_AUDIT_LOGS)),
):
    """Get audit logs by event type (admin only).

    Args:
        event_type: Event type to filter by
        limit: Maximum logs to return
        offset: Number of logs to skip
        current_user: Current authenticated admin user

    Returns:
        AuditLog with matching events

    Raises:
        HTTPException: If event type is invalid or user is not admin
    """
    try:
        filter_event_type = AuditEventType(event_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type: {event_type}"
        )

    return AuditLogger.get_logs_by_event_type(
        event_type=filter_event_type,
        limit=limit,
        offset=offset,
    )


@router.get("/logs/count")
def get_audit_log_count(
    current_user: User = Depends(require_permission(Permission.VIEW_AUDIT_LOGS)),
):
    """Get total number of audit logs (admin only).

    Args:
        current_user: Current authenticated admin user

    Returns:
        Count of audit logs

    Raises:
        HTTPException: If user is not an admin
    """
    return {
        "total": AuditLogger.get_log_count()
    }
