"""Request signing and verification for API integrity."""

import hmac
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import base64


class RequestSigner:
    """Sign and verify HTTP requests using HMAC-SHA256."""

    def __init__(self, secret_key: str, timestamp_tolerance_seconds: int = 300):
        """Initialize request signer.

        Args:
            secret_key: Secret key for signing (API key or shared secret)
            timestamp_tolerance_seconds: Max age of timestamp (prevents replay attacks)
        """
        self.secret_key = secret_key
        self.timestamp_tolerance = timedelta(seconds=timestamp_tolerance_seconds)

    def sign_request(
        self,
        method: str,
        path: str,
        body: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Sign a request with HMAC-SHA256.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            body: Request body (for POST/PUT)
            timestamp: ISO format timestamp (default: now)

        Returns:
            Tuple of (signature, timestamp)
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat() + "Z"

        # Create canonical request string
        canonical_request = self._create_canonical_request(method, path, body, timestamp)

        # Generate signature
        signature = hmac.new(
            self.secret_key.encode(),
            canonical_request.encode(),
            hashlib.sha256,
        ).hexdigest()

        return signature, timestamp

    def verify_request(
        self,
        method: str,
        path: str,
        signature: str,
        timestamp: str,
        body: Optional[str] = None,
    ) -> bool:
        """Verify a request signature.

        Args:
            method: HTTP method
            path: Request path
            signature: Provided signature
            timestamp: Request timestamp
            body: Request body

        Returns:
            True if signature is valid and timestamp is fresh, False otherwise
        """
        # Verify timestamp freshness
        if not self._verify_timestamp(timestamp):
            return False

        # Verify signature
        computed_signature, _ = self.sign_request(method, path, body, timestamp)

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, computed_signature)

    def _create_canonical_request(
        self,
        method: str,
        path: str,
        body: Optional[str],
        timestamp: str,
    ) -> str:
        """Create canonical request string for signing.

        Args:
            method: HTTP method
            path: Request path
            body: Request body
            timestamp: Request timestamp

        Returns:
            Canonical request string
        """
        # Build string to sign: METHOD\nPATH\nTIMESTAMP\nBODY
        parts = [method.upper(), path, timestamp]

        if body:
            # Use hash of body to avoid large request bodies
            body_hash = hashlib.sha256(body.encode()).hexdigest()
            parts.append(body_hash)
        else:
            parts.append("")

        return "\n".join(parts)

    def _verify_timestamp(self, timestamp_str: str) -> bool:
        """Verify timestamp is fresh.

        Args:
            timestamp_str: ISO format timestamp

        Returns:
            True if timestamp is recent, False if too old
        """
        try:
            # Remove 'Z' suffix and parse
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1]

            timestamp = datetime.fromisoformat(timestamp_str)
            now = datetime.utcnow()

            # Check if within tolerance
            age = now - timestamp
            if age.total_seconds() < 0:
                # Timestamp is in the future (too far)
                return False

            if age > self.timestamp_tolerance:
                # Timestamp is too old
                return False

            return True
        except (ValueError, AttributeError):
            return False


class SignatureValidator:
    """Validate signatures from headers."""

    def __init__(self, secret_key: str, timestamp_tolerance_seconds: int = 300):
        """Initialize validator.

        Args:
            secret_key: Secret key for verification
            timestamp_tolerance_seconds: Max age of timestamp
        """
        self.signer = RequestSigner(secret_key, timestamp_tolerance_seconds)

    def validate_from_headers(
        self,
        method: str,
        path: str,
        signature_header: Optional[str] = None,
        timestamp_header: Optional[str] = None,
        body: Optional[str] = None,
    ) -> bool:
        """Validate request signature from headers.

        Args:
            method: HTTP method
            path: Request path
            signature_header: X-Signature header value
            timestamp_header: X-Timestamp header value
            body: Request body

        Returns:
            True if valid, False otherwise
        """
        if not signature_header or not timestamp_header:
            return False

        return self.signer.verify_request(
            method=method,
            path=path,
            signature=signature_header,
            timestamp=timestamp_header,
            body=body,
        )

    def get_signing_headers(
        self,
        method: str,
        path: str,
        body: Optional[str] = None,
    ) -> Dict[str, str]:
        """Get headers needed for signing a request.

        Args:
            method: HTTP method
            path: Request path
            body: Request body

        Returns:
            Dictionary with X-Signature and X-Timestamp headers
        """
        signature, timestamp = self.signer.sign_request(method, path, body)

        return {
            "X-Signature": signature,
            "X-Timestamp": timestamp,
        }


# In-memory store for revoked timestamps (prevents replay after revocation)
_revoked_timestamps: Dict[str, datetime] = {}


def revoke_timestamp(timestamp: str) -> None:
    """Revoke a timestamp to prevent replay.

    Args:
        timestamp: ISO format timestamp to revoke
    """
    _revoked_timestamps[timestamp] = datetime.utcnow()


def is_timestamp_revoked(timestamp: str) -> bool:
    """Check if timestamp has been revoked.

    Args:
        timestamp: ISO format timestamp

    Returns:
        True if revoked, False otherwise
    """
    return timestamp in _revoked_timestamps


def clear_revoked_timestamps() -> None:
    """Clear revoked timestamps."""
    _revoked_timestamps.clear()


def cleanup_old_revocations(max_age_hours: int = 24) -> int:
    """Clean up old revoked timestamps.

    Args:
        max_age_hours: Maximum age of revocation record

    Returns:
        Number of records cleaned up
    """
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
    old_timestamps = [
        ts for ts, revoked_at in _revoked_timestamps.items()
        if revoked_at < cutoff
    ]

    for ts in old_timestamps:
        del _revoked_timestamps[ts]

    return len(old_timestamps)
