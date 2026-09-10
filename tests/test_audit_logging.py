"""Tests for audit logging functionality."""

import pytest
from datetime import datetime
from bedrock_poc.audit import AuditLogger, AuditEventType, AuditLog


class TestAuditLogging:
    """Test audit logging functionality."""

    def setup_method(self):
        """Clear logs before each test."""
        AuditLogger.clear_logs()

    def test_log_authentication_event(self):
        """Test logging authentication event."""
        entry = AuditLogger.log_authentication(
            user_id=1,
            user_email="user@example.com",
            ip_address="127.0.0.1",
            event_type=AuditEventType.LOGIN,
            status="success"
        )

        assert entry.event_type == AuditEventType.LOGIN
        assert entry.user_id == 1
        assert entry.user_email == "user@example.com"
        assert entry.ip_address == "127.0.0.1"
        assert entry.status == "success"

    def test_log_failed_authentication(self):
        """Test logging failed authentication."""
        entry = AuditLogger.log_authentication(
            user_email="user@example.com",
            ip_address="192.168.1.1",
            event_type=AuditEventType.LOGIN_FAILED,
            status="failure",
            error_message="Invalid password"
        )

        assert entry.event_type == AuditEventType.LOGIN_FAILED
        assert entry.status == "failure"
        assert entry.error_message == "Invalid password"

    def test_log_authorization_failure(self):
        """Test logging authorization failure."""
        entry = AuditLogger.log_authorization_failure(
            user_id=2,
            user_email="recruiter@example.com",
            ip_address="10.0.0.1",
            endpoint="/api/admin/users",
            method="GET",
            required_permission="MANAGE_USERS"
        )

        assert entry.event_type == AuditEventType.AUTHORIZATION_FAILED
        assert entry.user_id == 2
        assert entry.status == "failure"
        assert "MANAGE_USERS" in entry.error_message

    def test_log_data_modification(self):
        """Test logging data modification."""
        changes = {"role": "recruiter", "is_active": True}
        entry = AuditLogger.log_data_modification(
            event_type=AuditEventType.USER_CREATED,
            user_id=1,
            user_email="admin@example.com",
            resource_type="User",
            resource_id="123",
            action="create",
            changes=changes
        )

        assert entry.event_type == AuditEventType.USER_CREATED
        assert entry.resource_type == "User"
        assert entry.resource_id == "123"
        assert entry.changes == changes

    def test_log_api_access(self):
        """Test logging API access."""
        entry = AuditLogger.log_api_access(
            user_id=1,
            user_email="user@example.com",
            ip_address="127.0.0.1",
            endpoint="/api/candidates",
            method="GET",
            status_code=200,
            status="success"
        )

        assert entry.event_type == AuditEventType.API_ACCESS
        assert entry.endpoint == "/api/candidates"
        assert entry.method == "GET"
        assert entry.status_code == 200

    def test_get_logs_basic(self):
        """Test retrieving audit logs."""
        # Log some events
        AuditLogger.log_authentication(
            user_id=1,
            user_email="user@example.com",
            event_type=AuditEventType.LOGIN
        )
        AuditLogger.log_authentication(
            user_id=2,
            user_email="user2@example.com",
            event_type=AuditEventType.LOGIN
        )

        # Retrieve logs
        logs = AuditLogger.get_logs(limit=10)
        assert logs.total == 2
        assert len(logs.entries) == 2

    def test_get_logs_with_limit(self):
        """Test retrieving logs with limit."""
        for i in range(5):
            AuditLogger.log_authentication(user_id=i, user_email=f"user{i}@example.com")

        logs = AuditLogger.get_logs(limit=3)
        assert logs.total == 5
        assert len(logs.entries) == 3

    def test_get_logs_with_offset(self):
        """Test retrieving logs with offset."""
        for i in range(5):
            AuditLogger.log_authentication(user_id=i, user_email=f"user{i}@example.com")

        logs = AuditLogger.get_logs(limit=10, offset=2)
        assert logs.total == 5
        assert len(logs.entries) == 3

    def test_get_logs_by_event_type(self):
        """Test filtering logs by event type."""
        AuditLogger.log_authentication(user_id=1, event_type=AuditEventType.LOGIN)
        AuditLogger.log_authentication(user_id=2, event_type=AuditEventType.LOGIN_FAILED)
        AuditLogger.log_api_access(user_id=3)

        logs = AuditLogger.get_logs(event_type=AuditEventType.LOGIN)
        assert logs.total == 1
        assert logs.entries[0].event_type == AuditEventType.LOGIN

    def test_get_logs_by_user_id(self):
        """Test filtering logs by user ID."""
        AuditLogger.log_authentication(user_id=1, user_email="user1@example.com")
        AuditLogger.log_authentication(user_id=2, user_email="user2@example.com")
        AuditLogger.log_api_access(user_id=1)

        logs = AuditLogger.get_logs(user_id=1)
        assert logs.total == 2
        assert all(entry.user_id == 1 for entry in logs.entries)

    def test_get_logs_for_user(self):
        """Test getting logs for specific user."""
        AuditLogger.log_authentication(user_id=1, user_email="user1@example.com")
        AuditLogger.log_authentication(user_id=2, user_email="user2@example.com")
        AuditLogger.log_api_access(user_id=1)

        logs = AuditLogger.get_logs_for_user(user_id=1)
        assert logs.total == 2
        assert all(entry.user_id == 1 for entry in logs.entries)

    def test_get_logs_by_event_type_method(self):
        """Test get_logs_by_event_type method."""
        AuditLogger.log_authentication(event_type=AuditEventType.LOGIN)
        AuditLogger.log_authentication(event_type=AuditEventType.LOGIN_FAILED)
        AuditLogger.log_api_access()

        logs = AuditLogger.get_logs_by_event_type(AuditEventType.LOGIN)
        assert logs.total == 1
        assert logs.entries[0].event_type == AuditEventType.LOGIN

    def test_get_log_count(self):
        """Test getting total log count."""
        assert AuditLogger.get_log_count() == 0

        AuditLogger.log_authentication(user_id=1)
        assert AuditLogger.get_log_count() == 1

        AuditLogger.log_authentication(user_id=2)
        assert AuditLogger.get_log_count() == 2

    def test_clear_logs(self):
        """Test clearing all logs."""
        AuditLogger.log_authentication(user_id=1)
        AuditLogger.log_authentication(user_id=2)
        assert AuditLogger.get_log_count() == 2

        AuditLogger.clear_logs()
        assert AuditLogger.get_log_count() == 0

    def test_logs_sorted_by_timestamp_descending(self):
        """Test that logs are sorted by timestamp descending."""
        AuditLogger.log_authentication(user_id=1, user_email="user1@example.com")
        AuditLogger.log_authentication(user_id=2, user_email="user2@example.com")
        AuditLogger.log_authentication(user_id=3, user_email="user3@example.com")

        logs = AuditLogger.get_logs(limit=10)
        timestamps = [entry.timestamp for entry in logs.entries]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_audit_log_entry_fields(self):
        """Test that audit log entries contain all expected fields."""
        entry = AuditLogger.log_event(
            event_type=AuditEventType.DATA_CREATED,
            user_id=1,
            user_email="user@example.com",
            ip_address="127.0.0.1",
            endpoint="/api/jobs",
            method="POST",
            resource_type="Job",
            resource_id="job123",
            action="create",
            status="success",
            status_code=201,
            changes={"title": "Engineer"},
            metadata={"source": "api"}
        )

        assert entry.event_type == AuditEventType.DATA_CREATED
        assert entry.user_id == 1
        assert entry.user_email == "user@example.com"
        assert entry.ip_address == "127.0.0.1"
        assert entry.endpoint == "/api/jobs"
        assert entry.method == "POST"
        assert entry.resource_type == "Job"
        assert entry.resource_id == "job123"
        assert entry.action == "create"
        assert entry.status == "success"
        assert entry.status_code == 201
        assert entry.changes == {"title": "Engineer"}
        assert entry.metadata == {"source": "api"}

    def test_log_filtering_by_date_range(self):
        """Test filtering logs by date range."""
        start_time = datetime.utcnow()

        AuditLogger.log_authentication(user_id=1)
        AuditLogger.log_authentication(user_id=2)

        end_time = datetime.utcnow()

        logs = AuditLogger.get_logs(start_date=start_time, end_date=end_time)
        assert logs.total >= 2

    def test_audit_log_response_structure(self):
        """Test that AuditLog response has correct structure."""
        AuditLogger.log_authentication(user_id=1)

        logs = AuditLogger.get_logs()
        assert isinstance(logs, AuditLog)
        assert logs.total >= 1
        assert isinstance(logs.entries, list)
        assert len(logs.entries) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
