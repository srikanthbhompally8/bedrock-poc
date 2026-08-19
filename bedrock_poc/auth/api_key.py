"""API key authentication for service-to-service calls."""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from pydantic import BaseModel, Field, ConfigDict
from bedrock_poc.auth.models import UserRole


class APIKeyCreate(BaseModel):
    """Request model for creating API key."""
    name: str = Field(..., min_length=1, max_length=255, description="API key name")
    description: Optional[str] = Field(None, max_length=1000, description="API key description")
    expires_in_days: Optional[int] = Field(None, description="Days until expiration (None = never expires)")
    role: UserRole = Field(default=UserRole.CANDIDATE, description="Role for API key")


class APIKeyResponse(BaseModel):
    """Response model for API key."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str]
    key_preview: str = Field(..., description="First 8 characters of key for identification")
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    last_used_at: Optional[datetime]
    role: UserRole


class APIKeySecret(BaseModel):
    """Secret response with full key (only shown once)."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    api_key: str = Field(..., description="Full API key - SAVE THIS SECURELY")
    key_preview: str
    created_at: datetime
    expires_at: Optional[datetime]
    role: UserRole


# In-memory API key storage
_api_keys: Dict[str, Dict] = {}
_api_key_counter = 1


class APIKeyService:
    """Service for managing API keys."""

    @staticmethod
    def generate_key(length: int = 32) -> str:
        """Generate a secure random API key.

        Args:
            length: Length of key to generate

        Returns:
            Generated API key
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def create_api_key(
        user_id: int,
        name: str,
        description: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        role: UserRole = UserRole.CANDIDATE,
    ) -> Tuple[APIKeySecret, str]:
        """Create a new API key.

        Args:
            user_id: User ID that owns the key
            name: Name for the key
            description: Optional description
            expires_in_days: Days until expiration (None = never expires)
            role: Role for the key

        Returns:
            Tuple of (APIKeySecret, full_key)
        """
        global _api_key_counter

        # Generate key
        api_key = APIKeyService.generate_key()
        key_preview = api_key[:8]

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Store key hash (in production, hash the key)
        key_id = f"key_{_api_key_counter}"
        _api_key_counter += 1

        key_data = {
            "id": key_id,
            "user_id": user_id,
            "name": name,
            "description": description,
            "api_key_hash": api_key,  # In production, use hash
            "key_preview": key_preview,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "is_active": True,
            "last_used_at": None,
            "role": role.value,
        }

        _api_keys[key_id] = key_data

        secret = APIKeySecret(
            id=key_id,
            name=name,
            description=description,
            api_key=api_key,
            key_preview=key_preview,
            created_at=key_data["created_at"],
            expires_at=expires_at,
            role=role,
        )

        return secret, api_key

    @staticmethod
    def verify_api_key(api_key: str) -> Optional[Dict]:
        """Verify an API key and return its data.

        Args:
            api_key: API key to verify

        Returns:
            API key data if valid, None otherwise
        """
        for key_id, key_data in _api_keys.items():
            if key_data["api_key_hash"] == api_key:  # In production, use hash comparison
                # Check if active
                if not key_data["is_active"]:
                    return None

                # Check if expired
                if key_data["expires_at"] and key_data["expires_at"] < datetime.utcnow():
                    return None

                # Update last used time
                key_data["last_used_at"] = datetime.utcnow()
                return key_data

        return None

    @staticmethod
    def get_api_key(key_id: str) -> Optional[APIKeyResponse]:
        """Get API key details (without the secret).

        Args:
            key_id: ID of the key

        Returns:
            APIKeyResponse if found, None otherwise
        """
        if key_id not in _api_keys:
            return None

        key_data = _api_keys[key_id]
        return APIKeyResponse(
            id=key_id,
            name=key_data["name"],
            description=key_data["description"],
            key_preview=key_data["key_preview"],
            created_at=key_data["created_at"],
            expires_at=key_data["expires_at"],
            is_active=key_data["is_active"],
            last_used_at=key_data["last_used_at"],
            role=UserRole(key_data["role"]),
        )

    @staticmethod
    def list_api_keys(user_id: int) -> list[APIKeyResponse]:
        """List all API keys for a user.

        Args:
            user_id: User ID

        Returns:
            List of API keys
        """
        keys = []
        for key_id, key_data in _api_keys.items():
            if key_data["user_id"] == user_id:
                keys.append(APIKeyResponse(
                    id=key_id,
                    name=key_data["name"],
                    description=key_data["description"],
                    key_preview=key_data["key_preview"],
                    created_at=key_data["created_at"],
                    expires_at=key_data["expires_at"],
                    is_active=key_data["is_active"],
                    last_used_at=key_data["last_used_at"],
                    role=UserRole(key_data["role"]),
                ))
        return keys

    @staticmethod
    def revoke_api_key(key_id: str) -> bool:
        """Revoke an API key.

        Args:
            key_id: ID of the key to revoke

        Returns:
            True if revoked, False if not found
        """
        if key_id not in _api_keys:
            return False

        _api_keys[key_id]["is_active"] = False
        return True

    @staticmethod
    def delete_api_key(key_id: str) -> bool:
        """Delete an API key.

        Args:
            key_id: ID of the key to delete

        Returns:
            True if deleted, False if not found
        """
        if key_id not in _api_keys:
            return False

        del _api_keys[key_id]
        return True

    @staticmethod
    def rotate_api_key(key_id: str) -> Optional[Tuple[APIKeySecret, str]]:
        """Rotate an API key (create new, revoke old).

        Args:
            key_id: ID of the key to rotate

        Returns:
            Tuple of (new_secret, new_key) or None if not found
        """
        if key_id not in _api_keys:
            return None

        old_key_data = _api_keys[key_id]

        # Create new key with same settings
        new_secret, new_key = APIKeyService.create_api_key(
            user_id=old_key_data["user_id"],
            name=old_key_data["name"],
            description=old_key_data["description"],
            expires_in_days=None,  # Use current expiration as-is
            role=UserRole(old_key_data["role"]),
        )

        # Revoke old key
        old_key_data["is_active"] = False

        return new_secret, new_key
