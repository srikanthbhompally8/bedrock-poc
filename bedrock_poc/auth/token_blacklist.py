"""Token revocation and blacklisting for logout functionality."""

from datetime import datetime, timedelta
from typing import Set, Dict


class TokenBlacklist:
    """In-memory token blacklist for tracking revoked tokens."""

    def __init__(self):
        # Store blacklisted tokens with expiration for cleanup
        self.blacklist: Dict[str, datetime] = {}
        self.last_cleanup = datetime.utcnow()
        self.cleanup_interval = timedelta(hours=1)

    def add_token(self, token: str, expires_at: datetime) -> None:
        """Add a token to the blacklist.

        Args:
            token: JWT token to blacklist
            expires_at: When the token expires (cleanup after this)
        """
        self.blacklist[token] = expires_at

        # Periodic cleanup
        if datetime.utcnow() - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired()
            self.last_cleanup = datetime.utcnow()

    def is_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted.

        Args:
            token: JWT token to check

        Returns:
            True if blacklisted, False otherwise
        """
        if token not in self.blacklist:
            return False

        expires_at = self.blacklist[token]

        # Token is no longer blacklisted if it has expired
        if expires_at < datetime.utcnow():
            del self.blacklist[token]
            return False

        return True

    def revoke_token(self, token: str, expires_at: datetime) -> bool:
        """Revoke (blacklist) a token.

        Args:
            token: JWT token to revoke
            expires_at: When the token expires

        Returns:
            True if revoked, False if already revoked
        """
        if token in self.blacklist:
            return False  # Already revoked

        self.add_token(token, expires_at)
        return True

    def _cleanup_expired(self) -> None:
        """Remove expired tokens from blacklist."""
        now = datetime.utcnow()
        expired_tokens = [
            token for token, expires_at in self.blacklist.items()
            if expires_at < now
        ]

        for token in expired_tokens:
            del self.blacklist[token]

    def clear_user_tokens(self, user_id: int = None) -> int:
        """Clear all tokens (optionally for a specific user).

        Note: Without decoding tokens, we can't filter by user_id efficiently.
        In production, store user_id in token and decode it first.

        Args:
            user_id: Optional user ID (not used in this implementation)

        Returns:
            Number of tokens cleared
        """
        count = len(self.blacklist)
        self.blacklist.clear()
        return count

    def get_blacklist_size(self) -> int:
        """Get current number of blacklisted tokens."""
        return len(self.blacklist)

    def reset(self) -> None:
        """Clear all blacklisted tokens."""
        self.blacklist.clear()


# Global token blacklist instance
_token_blacklist = TokenBlacklist()


def get_token_blacklist() -> TokenBlacklist:
    """Get the global token blacklist instance."""
    return _token_blacklist
