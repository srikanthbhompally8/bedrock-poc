"""Rate limiting for authentication endpoints."""

from datetime import datetime, timedelta
from typing import Dict, Tuple
from collections import defaultdict
from fastapi import HTTPException, status


class RateLimiter:
    """Simple in-memory rate limiter for authentication endpoints."""

    def __init__(self):
        # Store: {endpoint_key: [(timestamp, count)]}
        self.requests: Dict[str, list[Tuple[datetime, int]]] = defaultdict(list)
        self.cleanup_interval = timedelta(minutes=5)
        self.last_cleanup = datetime.utcnow()

    def is_allowed(
        self,
        identifier: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        """Check if request is allowed based on rate limit.

        Args:
            identifier: Unique identifier (IP, user_id, email)
            endpoint: API endpoint name
            max_requests: Max requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            True if request is allowed, False if rate limited

        Raises:
            HTTPException: If rate limit exceeded
        """
        key = f"{endpoint}:{identifier}"
        now = datetime.utcnow()

        # Cleanup old requests periodically
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_requests(now)
            self.last_cleanup = now

        # Get requests in current window
        if key not in self.requests:
            self.requests[key] = []

        # Remove requests outside the window
        cutoff = now - timedelta(seconds=window_seconds)
        self.requests[key] = [
            (ts, count) for ts, count in self.requests[key]
            if ts > cutoff
        ]

        # Count requests in window
        total_requests = sum(count for _, count in self.requests[key])

        # Check if limit exceeded
        if total_requests >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(window_seconds)},
            )

        # Add current request
        if self.requests[key] and self.requests[key][-1][0] == now:
            # Increment count for this second
            ts, count = self.requests[key][-1]
            self.requests[key][-1] = (ts, count + 1)
        else:
            # Add new timestamp
            self.requests[key].append((now, 1))

        return True

    def get_remaining_requests(
        self,
        identifier: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int,
    ) -> int:
        """Get remaining requests for identifier.

        Args:
            identifier: Unique identifier
            endpoint: API endpoint name
            max_requests: Max requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Number of remaining requests
        """
        key = f"{endpoint}:{identifier}"
        now = datetime.utcnow()

        if key not in self.requests:
            return max_requests

        # Remove requests outside the window
        cutoff = now - timedelta(seconds=window_seconds)
        self.requests[key] = [
            (ts, count) for ts, count in self.requests[key]
            if ts > cutoff
        ]

        # Count requests in window
        total_requests = sum(count for _, count in self.requests[key])
        return max(0, max_requests - total_requests)

    def _cleanup_old_requests(self, now: datetime = None) -> None:
        """Clean up old request records.

        Args:
            now: Current time (defaults to utcnow)
        """
        if now is None:
            now = datetime.utcnow()

        cutoff = now - timedelta(hours=1)

        keys_to_remove = []
        for key, requests in self.requests.items():
            # Keep only recent requests
            self.requests[key] = [
                (ts, count) for ts, count in requests
                if ts > cutoff
            ]
            # Remove keys with no requests
            if not self.requests[key]:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.requests[key]

    def reset(self, identifier: str = None, endpoint: str = None) -> None:
        """Reset rate limit counters.

        Args:
            identifier: Specific identifier to reset (None = all)
            endpoint: Specific endpoint to reset (None = all)
        """
        if identifier is None and endpoint is None:
            # Reset all
            self.requests.clear()
        elif identifier and endpoint:
            # Reset specific endpoint:identifier
            key = f"{endpoint}:{identifier}"
            if key in self.requests:
                del self.requests[key]
        elif endpoint:
            # Reset all for endpoint
            keys_to_remove = [k for k in self.requests if k.startswith(f"{endpoint}:")]
            for key in keys_to_remove:
                del self.requests[key]


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter
