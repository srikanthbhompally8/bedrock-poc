"""Tests for API key authentication and management."""

import pytest
from fastapi import status
from bedrock_poc.auth import (
    APIKeyService,
    APIKeyCreate,
    UserRole,
)


class TestAPIKeyGeneration:
    """Test API key generation."""

    def test_generate_key(self):
        """Test generating an API key."""
        key = APIKeyService.generate_key()
        assert key is not None
        assert len(key) > 0
        assert isinstance(key, str)

    def test_generate_different_keys(self):
        """Test that generated keys are unique."""
        key1 = APIKeyService.generate_key()
        key2 = APIKeyService.generate_key()
        assert key1 != key2


class TestAPIKeyManagement:
    """Test API key management operations."""

    def setup_method(self):
        """Setup test environment."""
        # Clear any existing keys for testing
        from bedrock_poc.auth.api_key import _api_keys
        _api_keys.clear()

    def test_create_api_key(self):
        """Test creating an API key."""
        secret, key = APIKeyService.create_api_key(
            user_id=1,
            name="Test Key",
            description="Test API key",
            expires_in_days=30,
            role=UserRole.RECRUITER,
        )

        assert secret is not None
        assert secret.name == "Test Key"
        assert secret.description == "Test API key"
        assert secret.role == UserRole.RECRUITER
        assert secret.key_preview == key[:8]
        assert secret.id is not None
        assert secret.expires_at is not None

    def test_create_api_key_no_expiration(self):
        """Test creating API key without expiration."""
        secret, key = APIKeyService.create_api_key(
            user_id=1,
            name="No Expiry Key",
            role=UserRole.CANDIDATE,
        )

        assert secret.expires_at is None

    def test_verify_api_key_valid(self):
        """Test verifying a valid API key."""
        secret, key = APIKeyService.create_api_key(
            user_id=1,
            name="Test Key",
            role=UserRole.RECRUITER,
        )

        # Verify the key
        key_data = APIKeyService.verify_api_key(key)
        assert key_data is not None
        assert key_data["user_id"] == 1
        assert key_data["is_active"]

    def test_verify_api_key_invalid(self):
        """Test verifying an invalid API key."""
        key_data = APIKeyService.verify_api_key("invalid_key")
        assert key_data is None

    def test_get_api_key(self):
        """Test retrieving API key details."""
        secret, key = APIKeyService.create_api_key(
            user_id=1,
            name="Test Key",
            role=UserRole.RECRUITER,
        )

        retrieved = APIKeyService.get_api_key(secret.id)
        assert retrieved is not None
        assert retrieved.name == "Test Key"
        assert retrieved.id == secret.id
        assert retrieved.role == UserRole.RECRUITER

    def test_list_api_keys_for_user(self):
        """Test listing API keys for a user."""
        # Create 3 keys for user 1
        for i in range(3):
            APIKeyService.create_api_key(
                user_id=1,
                name=f"Key {i}",
                role=UserRole.RECRUITER,
            )

        # Create 2 keys for user 2
        for i in range(2):
            APIKeyService.create_api_key(
                user_id=2,
                name=f"User2 Key {i}",
                role=UserRole.CANDIDATE,
            )

        # List keys for user 1
        user1_keys = APIKeyService.list_api_keys(1)
        assert len(user1_keys) == 3

        # List keys for user 2
        user2_keys = APIKeyService.list_api_keys(2)
        assert len(user2_keys) == 2

    def test_revoke_api_key(self):
        """Test revoking an API key."""
        secret, key = APIKeyService.create_api_key(
            user_id=1,
            name="Test Key",
            role=UserRole.RECRUITER,
        )

        # Verify key works
        key_data = APIKeyService.verify_api_key(key)
        assert key_data is not None

        # Revoke key
        success = APIKeyService.revoke_api_key(secret.id)
        assert success

        # Verify revoked key doesn't work
        key_data = APIKeyService.verify_api_key(key)
        assert key_data is None

    def test_delete_api_key(self):
        """Test deleting an API key."""
        secret, key = APIKeyService.create_api_key(
            user_id=1,
            name="Test Key",
            role=UserRole.RECRUITER,
        )

        # Delete key
        success = APIKeyService.delete_api_key(secret.id)
        assert success

        # Verify key is gone
        retrieved = APIKeyService.get_api_key(secret.id)
        assert retrieved is None

    def test_rotate_api_key(self):
        """Test rotating an API key."""
        secret, old_key = APIKeyService.create_api_key(
            user_id=1,
            name="Test Key",
            role=UserRole.RECRUITER,
        )

        # Rotate key
        result = APIKeyService.rotate_api_key(secret.id)
        assert result is not None

        new_secret, new_key = result

        # Old key should not work
        old_key_data = APIKeyService.verify_api_key(old_key)
        assert old_key_data is None

        # New key should work
        new_key_data = APIKeyService.verify_api_key(new_key)
        assert new_key_data is not None
        assert new_key_data["user_id"] == 1

    def test_api_key_preview(self):
        """Test that key preview matches first 8 characters."""
        secret, key = APIKeyService.create_api_key(
            user_id=1,
            name="Test Key",
            role=UserRole.RECRUITER,
        )

        assert secret.key_preview == key[:8]

    def test_api_key_different_roles(self):
        """Test creating keys with different roles."""
        # Create admin key
        admin_secret, _ = APIKeyService.create_api_key(
            user_id=1,
            name="Admin Key",
            role=UserRole.ADMIN,
        )
        assert admin_secret.role == UserRole.ADMIN

        # Create recruiter key
        recruiter_secret, _ = APIKeyService.create_api_key(
            user_id=1,
            name="Recruiter Key",
            role=UserRole.RECRUITER,
        )
        assert recruiter_secret.role == UserRole.RECRUITER

        # Create candidate key
        candidate_secret, _ = APIKeyService.create_api_key(
            user_id=1,
            name="Candidate Key",
            role=UserRole.CANDIDATE,
        )
        assert candidate_secret.role == UserRole.CANDIDATE


class TestAPIKeySecurity:
    """Test API key security features."""

    def setup_method(self):
        """Setup test environment."""
        from bedrock_poc.auth.api_key import _api_keys
        _api_keys.clear()

    def test_expired_key_rejected(self):
        """Test that expired keys are rejected."""
        from datetime import datetime, timedelta

        secret, key = APIKeyService.create_api_key(
            user_id=1,
            name="Expiring Key",
            expires_in_days=1,
            role=UserRole.RECRUITER,
        )

        # Manually set expiration to past
        from bedrock_poc.auth.api_key import _api_keys
        for k in _api_keys.values():
            if k["id"] == secret.id:
                k["expires_at"] = datetime.utcnow() - timedelta(hours=1)
                break

        # Verify key is rejected
        key_data = APIKeyService.verify_api_key(key)
        assert key_data is None

    def test_last_used_timestamp_updated(self):
        """Test that last_used_at is updated on verification."""
        secret, key = APIKeyService.create_api_key(
            user_id=1,
            name="Test Key",
            role=UserRole.RECRUITER,
        )

        # Get initial last_used_at (should be None)
        from bedrock_poc.auth.api_key import _api_keys
        initial_key_data = _api_keys[secret.id]
        assert initial_key_data["last_used_at"] is None

        # Verify key
        APIKeyService.verify_api_key(key)

        # Check last_used_at is updated
        updated_key_data = _api_keys[secret.id]
        assert updated_key_data["last_used_at"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
