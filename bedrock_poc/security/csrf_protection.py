"""CSRF (Cross-Site Request Forgery) protection."""

import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from hashlib import sha256


class CSRFTokenManager:
    """Manage CSRF tokens for protection against cross-site forgery attacks."""

    def __init__(self, token_expiration_hours: int = 24):
        # Store: {token: {session_id, expires_at, ip_address}}
        self.tokens: Dict[str, Dict] = {}
        self.token_expiration = timedelta(hours=token_expiration_hours)
        self.last_cleanup = datetime.utcnow()
        self.cleanup_interval = timedelta(hours=1)

    def generate_token(self, session_id: str, ip_address: str = None) -> str:
        """Generate a new CSRF token.

        Args:
            session_id: User session identifier
            ip_address: Optional IP address for additional validation

        Returns:
            Generated CSRF token
        """
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + self.token_expiration

        self.tokens[token] = {
            "session_id": session_id,
            "ip_address": ip_address,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "used": False,
        }

        # Periodic cleanup
        if datetime.utcnow() - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired()
            self.last_cleanup = datetime.utcnow()

        return token

    def validate_token(
        self,
        token: str,
        session_id: str,
        ip_address: str = None,
        consume_token: bool = True,
    ) -> bool:
        """Validate a CSRF token.

        Args:
            token: Token to validate
            session_id: User session ID
            ip_address: Optional IP address for validation
            consume_token: Whether to mark token as used (one-time use)

        Returns:
            True if valid, False otherwise
        """
        if token not in self.tokens:
            return False

        token_data = self.tokens[token]

        # Check session ID matches
        if token_data["session_id"] != session_id:
            return False

        # Check if expired
        if token_data["expires_at"] < datetime.utcnow():
            del self.tokens[token]
            return False

        # Check if already used
        if token_data["used"]:
            return False

        # Optional: Check IP address matches
        if ip_address and token_data["ip_address"] and token_data["ip_address"] != ip_address:
            return False

        # Mark as used if requested
        if consume_token:
            token_data["used"] = True

        return True

    def invalidate_token(self, token: str) -> bool:
        """Invalidate a token.

        Args:
            token: Token to invalidate

        Returns:
            True if invalidated, False if not found
        """
        if token not in self.tokens:
            return False

        del self.tokens[token]
        return True

    def invalidate_session_tokens(self, session_id: str) -> int:
        """Invalidate all tokens for a session.

        Args:
            session_id: Session ID

        Returns:
            Number of tokens invalidated
        """
        tokens_to_remove = [
            token for token, data in self.tokens.items()
            if data["session_id"] == session_id
        ]

        for token in tokens_to_remove:
            del self.tokens[token]

        return len(tokens_to_remove)

    def _cleanup_expired(self) -> None:
        """Remove expired tokens."""
        now = datetime.utcnow()
        expired_tokens = [
            token for token, data in self.tokens.items()
            if data["expires_at"] < now
        ]

        for token in expired_tokens:
            del self.tokens[token]

    def get_token_count(self) -> int:
        """Get number of active tokens."""
        return len(self.tokens)

    def reset(self) -> None:
        """Clear all tokens."""
        self.tokens.clear()


# Global CSRF token manager
_csrf_manager = CSRFTokenManager()


def get_csrf_manager() -> CSRFTokenManager:
    """Get the global CSRF token manager."""
    return _csrf_manager


# Session management (simple in-memory for now)
_sessions: Dict[str, Dict] = {}


def create_session(user_id: int, ip_address: str = None) -> str:
    """Create a new session.

    Args:
        user_id: User ID
        ip_address: Client IP address

    Returns:
        Session ID
    """
    session_id = secrets.token_urlsafe(32)
    _sessions[session_id] = {
        "user_id": user_id,
        "ip_address": ip_address,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24),
    }
    return session_id


def validate_session(session_id: str) -> Optional[int]:
    """Validate session and return user ID.

    Args:
        session_id: Session ID

    Returns:
        User ID if valid, None otherwise
    """
    if session_id not in _sessions:
        return None

    session_data = _sessions[session_id]

    # Check if expired
    if session_data["expires_at"] < datetime.utcnow():
        del _sessions[session_id]
        return None

    return session_data["user_id"]


def invalidate_session(session_id: str) -> bool:
    """Invalidate a session.

    Args:
        session_id: Session ID

    Returns:
        True if invalidated, False if not found
    """
    if session_id not in _sessions:
        return False

    del _sessions[session_id]
    # Also invalidate CSRF tokens for this session
    _csrf_manager.invalidate_session_tokens(session_id)
    return True
