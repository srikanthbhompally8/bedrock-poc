"""Tests for token revocation and blacklisting functionality."""

import pytest
from datetime import datetime, timedelta
from bedrock_poc.auth import (
    AuthService,
    UserService,
    UserCreate,
    UserRole,
    get_token_blacklist,
)


class TestTokenBlacklist:
    """Test token blacklist functionality."""

    def setup_method(self):
        """Reset blacklist before each test."""
        blacklist = get_token_blacklist()
        blacklist.reset()

    def test_add_token_to_blacklist(self):
        """Test adding a token to blacklist."""
        blacklist = get_token_blacklist()
        token = "test_token_123"
        expires_at = datetime.utcnow() + timedelta(hours=1)

        blacklist.add_token(token, expires_at)
        assert blacklist.is_blacklisted(token)

    def test_blacklisted_token_is_not_valid(self):
        """Test that blacklisted token is rejected."""
        blacklist = get_token_blacklist()
        token = "test_token_123"
        expires_at = datetime.utcnow() + timedelta(hours=1)

        blacklist.add_token(token, expires_at)
        assert blacklist.is_blacklisted(token)

    def test_expired_token_removed_from_blacklist(self):
        """Test that expired tokens are cleaned up."""
        blacklist = get_token_blacklist()
        token = "expired_token"
        # Set expiration to past
        expires_at = datetime.utcnow() - timedelta(hours=1)

        blacklist.add_token(token, expires_at)
        # After cleanup, expired token should not be blacklisted
        assert not blacklist.is_blacklisted(token)

    def test_revoke_token(self):
        """Test revoking a token."""
        blacklist = get_token_blacklist()
        token = "revoke_token"
        expires_at = datetime.utcnow() + timedelta(hours=1)

        success = blacklist.revoke_token(token, expires_at)
        assert success
        assert blacklist.is_blacklisted(token)

    def test_revoke_same_token_twice(self):
        """Test that revoking same token twice fails."""
        blacklist = get_token_blacklist()
        token = "revoke_token"
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # First revocation succeeds
        success1 = blacklist.revoke_token(token, expires_at)
        assert success1

        # Second revocation fails (already revoked)
        success2 = blacklist.revoke_token(token, expires_at)
        assert not success2

    def test_clear_blacklist(self):
        """Test clearing all blacklisted tokens."""
        blacklist = get_token_blacklist()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Add multiple tokens
        for i in range(5):
            blacklist.add_token(f"token_{i}", expires_at)

        # Clear blacklist
        blacklist.reset()

        # All tokens should be gone
        for i in range(5):
            assert not blacklist.is_blacklisted(f"token_{i}")

    def test_get_blacklist_size(self):
        """Test getting blacklist size."""
        blacklist = get_token_blacklist()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        assert blacklist.get_blacklist_size() == 0

        # Add tokens
        for i in range(3):
            blacklist.add_token(f"token_{i}", expires_at)

        assert blacklist.get_blacklist_size() == 3

    def test_different_tokens_tracked_separately(self):
        """Test that different tokens are tracked separately."""
        blacklist = get_token_blacklist()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        token1 = "token_1"
        token2 = "token_2"

        blacklist.add_token(token1, expires_at)
        blacklist.add_token(token2, expires_at)

        assert blacklist.is_blacklisted(token1)
        assert blacklist.is_blacklisted(token2)


class TestAuthServiceTokenRevocation:
    """Test AuthService token revocation."""

    def setup_method(self):
        """Setup before each test."""
        blacklist = get_token_blacklist()
        blacklist.reset()

    def test_revoke_invalid_token(self):
        """Test revoking an invalid token."""
        success = AuthService.revoke_token("invalid_token")
        assert not success


class TestTokenBlacklistIntegration:
    """Integration tests for token blacklist."""

    def setup_method(self):
        """Setup before each test."""
        blacklist = get_token_blacklist()
        blacklist.reset()


class TestTokenExpirationAndCleanup:
    """Test token expiration and cleanup."""

    def setup_method(self):
        """Setup before each test."""
        blacklist = get_token_blacklist()
        blacklist.reset()

    def test_cleanup_removes_expired_tokens(self):
        """Test that cleanup removes expired tokens."""
        blacklist = get_token_blacklist()

        # Add expired token
        expired_token = "expired_token"
        expires_at = datetime.utcnow() - timedelta(hours=1)
        blacklist.add_token(expired_token, expires_at)

        # Add active token
        active_token = "active_token"
        expires_at = datetime.utcnow() + timedelta(hours=1)
        blacklist.add_token(active_token, expires_at)

        # Check expired token is cleaned up
        assert not blacklist.is_blacklisted(expired_token)
        assert blacklist.is_blacklisted(active_token)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
