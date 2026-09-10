"""Tests for CSRF protection."""

import pytest
from datetime import datetime, timedelta
from bedrock_poc.security import (
    get_csrf_manager,
    create_session,
    validate_session,
    invalidate_session,
)


class TestCSRFTokenGeneration:
    """Test CSRF token generation."""

    def setup_method(self):
        """Reset manager before each test."""
        manager = get_csrf_manager()
        manager.reset()

    def test_generate_token(self):
        """Test generating a CSRF token."""
        manager = get_csrf_manager()
        session_id = "test_session_123"

        token = manager.generate_token(session_id)
        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)

    def test_generate_different_tokens(self):
        """Test that generated tokens are unique."""
        manager = get_csrf_manager()
        session_id = "test_session"

        token1 = manager.generate_token(session_id)
        token2 = manager.generate_token(session_id)
        assert token1 != token2

    def test_token_stored_with_metadata(self):
        """Test that token is stored with session info."""
        manager = get_csrf_manager()
        session_id = "test_session"
        ip_address = "192.168.1.1"

        token = manager.generate_token(session_id, ip_address)
        assert manager.tokens[token]["session_id"] == session_id
        assert manager.tokens[token]["ip_address"] == ip_address


class TestCSRFTokenValidation:
    """Test CSRF token validation."""

    def setup_method(self):
        """Reset manager before each test."""
        manager = get_csrf_manager()
        manager.reset()

    def test_validate_valid_token(self):
        """Test validating a valid token."""
        manager = get_csrf_manager()
        session_id = "test_session"

        token = manager.generate_token(session_id)
        assert manager.validate_token(token, session_id)

    def test_validate_invalid_token(self):
        """Test validating an invalid token."""
        manager = get_csrf_manager()
        session_id = "test_session"

        assert not manager.validate_token("invalid_token", session_id)

    def test_validate_token_wrong_session(self):
        """Test validating token with wrong session ID."""
        manager = get_csrf_manager()
        session_id = "test_session"

        token = manager.generate_token(session_id)
        assert not manager.validate_token(token, "different_session")

    def test_validate_expired_token(self):
        """Test validating an expired token."""
        manager = get_csrf_manager()
        session_id = "test_session"

        token = manager.generate_token(session_id)
        # Manually set expiration to past
        manager.tokens[token]["expires_at"] = datetime.utcnow() - timedelta(hours=1)

        assert not manager.validate_token(token, session_id)

    def test_token_consumed_after_validation(self):
        """Test that token is marked as used after validation."""
        manager = get_csrf_manager()
        session_id = "test_session"

        token = manager.generate_token(session_id)
        # First validation should succeed
        assert manager.validate_token(token, session_id, consume_token=True)

        # Second validation should fail (already used)
        assert not manager.validate_token(token, session_id)

    def test_token_not_consumed_when_flag_false(self):
        """Test that token is not marked as used when consume_token=False."""
        manager = get_csrf_manager()
        session_id = "test_session"

        token = manager.generate_token(session_id)
        # Validate without consuming
        assert manager.validate_token(token, session_id, consume_token=False)

        # Should still be valid for another validation
        assert manager.validate_token(token, session_id, consume_token=False)

    def test_ip_address_validation(self):
        """Test IP address validation."""
        manager = get_csrf_manager()
        session_id = "test_session"
        ip_address = "192.168.1.1"

        token = manager.generate_token(session_id, ip_address)
        # Validate with same IP
        assert manager.validate_token(token, session_id, ip_address=ip_address)

        # Validate with different IP should fail
        assert not manager.validate_token(token, session_id, ip_address="10.0.0.1")


class TestCSRFTokenManagement:
    """Test CSRF token management operations."""

    def setup_method(self):
        """Reset manager before each test."""
        manager = get_csrf_manager()
        manager.reset()

    def test_invalidate_token(self):
        """Test invalidating a token."""
        manager = get_csrf_manager()
        session_id = "test_session"

        token = manager.generate_token(session_id)
        assert manager.invalidate_token(token)
        assert not manager.validate_token(token, session_id)

    def test_invalidate_nonexistent_token(self):
        """Test invalidating a token that doesn't exist."""
        manager = get_csrf_manager()
        assert not manager.invalidate_token("nonexistent_token")

    def test_invalidate_session_tokens(self):
        """Test invalidating all tokens for a session."""
        manager = get_csrf_manager()
        session_id = "test_session"

        # Create 3 tokens for the session
        token1 = manager.generate_token(session_id)
        token2 = manager.generate_token(session_id)
        token3 = manager.generate_token(session_id)

        # Invalidate all session tokens
        count = manager.invalidate_session_tokens(session_id)
        assert count == 3

        # All tokens should be invalid
        assert not manager.validate_token(token1, session_id)
        assert not manager.validate_token(token2, session_id)
        assert not manager.validate_token(token3, session_id)

    def test_get_token_count(self):
        """Test getting token count."""
        manager = get_csrf_manager()
        session_id = "test_session"

        assert manager.get_token_count() == 0

        manager.generate_token(session_id)
        assert manager.get_token_count() == 1

        manager.generate_token(session_id)
        assert manager.get_token_count() == 2

    def test_reset_all_tokens(self):
        """Test resetting all tokens."""
        manager = get_csrf_manager()
        session_id = "test_session"

        manager.generate_token(session_id)
        manager.generate_token(session_id)
        assert manager.get_token_count() == 2

        manager.reset()
        assert manager.get_token_count() == 0


class TestSessionManagement:
    """Test session management."""

    def setup_method(self):
        """Reset manager and sessions before each test."""
        manager = get_csrf_manager()
        manager.reset()
        from bedrock_poc.security.csrf_protection import _sessions
        _sessions.clear()

    def test_create_session(self):
        """Test creating a session."""
        user_id = 1
        session_id = create_session(user_id)
        assert session_id is not None
        assert len(session_id) > 0

    def test_validate_session(self):
        """Test validating a session."""
        user_id = 1
        session_id = create_session(user_id)

        validated_user_id = validate_session(session_id)
        assert validated_user_id == user_id

    def test_validate_invalid_session(self):
        """Test validating an invalid session."""
        assert validate_session("invalid_session") is None

    def test_invalidate_session(self):
        """Test invalidating a session."""
        user_id = 1
        session_id = create_session(user_id)

        assert invalidate_session(session_id)
        assert validate_session(session_id) is None

    def test_session_invalidates_csrf_tokens(self):
        """Test that invalidating session also invalidates its CSRF tokens."""
        manager = get_csrf_manager()
        user_id = 1
        session_id = create_session(user_id)

        # Create CSRF token for session
        csrf_token = manager.generate_token(session_id)
        assert manager.validate_token(csrf_token, session_id)

        # Invalidate session
        invalidate_session(session_id)

        # CSRF token should no longer be valid
        assert not manager.validate_token(csrf_token, session_id)


class TestCSRFCleanup:
    """Test CSRF token cleanup."""

    def setup_method(self):
        """Reset manager before each test."""
        manager = get_csrf_manager()
        manager.reset()

    def test_expired_tokens_cleaned_up(self):
        """Test that expired tokens are cleaned up."""
        manager = get_csrf_manager()
        session_id = "test_session"

        # Create an expired token
        token = manager.generate_token(session_id)
        manager.tokens[token]["expires_at"] = datetime.utcnow() - timedelta(hours=1)

        # Attempt to validate (should trigger cleanup)
        assert not manager.validate_token(token, session_id)

        # Token should be removed
        assert token not in manager.tokens


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
