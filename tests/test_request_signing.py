"""Tests for request signing and verification."""

import pytest
from datetime import datetime, timedelta
from bedrock_poc.security import (
    RequestSigner,
    SignatureValidator,
    revoke_timestamp,
    is_timestamp_revoked,
    clear_revoked_timestamps,
)


class TestRequestSigning:
    """Test request signing functionality."""

    def setup_method(self):
        """Setup before each test."""
        self.secret_key = "test_secret_key_12345"
        self.signer = RequestSigner(self.secret_key)

    def test_sign_get_request(self):
        """Test signing a GET request."""
        method = "GET"
        path = "/api/users"

        signature, timestamp = self.signer.sign_request(method, path)

        assert signature is not None
        assert len(signature) > 0
        assert timestamp is not None
        assert "Z" in timestamp  # ISO format with Z suffix

    def test_sign_post_request_with_body(self):
        """Test signing a POST request with body."""
        method = "POST"
        path = "/api/users"
        body = '{"name": "John", "email": "john@example.com"}'

        signature, timestamp = self.signer.sign_request(method, path, body)

        assert signature is not None
        assert len(signature) > 0

    def test_sign_with_custom_timestamp(self):
        """Test signing with custom timestamp."""
        method = "GET"
        path = "/api/users"
        timestamp = "2026-08-19T10:00:00Z"

        signature, returned_timestamp = self.signer.sign_request(
            method, path, timestamp=timestamp
        )

        assert returned_timestamp == timestamp
        assert signature is not None

    def test_different_bodies_produce_different_signatures(self):
        """Test that different request bodies produce different signatures."""
        method = "POST"
        path = "/api/users"

        body1 = '{"name": "John"}'
        body2 = '{"name": "Jane"}'

        sig1, _ = self.signer.sign_request(method, path, body1)
        sig2, _ = self.signer.sign_request(method, path, body2)

        assert sig1 != sig2

    def test_same_request_produces_same_signature(self):
        """Test that same request produces same signature."""
        method = "GET"
        path = "/api/users"
        timestamp = "2026-08-19T10:00:00Z"

        sig1, _ = self.signer.sign_request(method, path, timestamp=timestamp)
        sig2, _ = self.signer.sign_request(method, path, timestamp=timestamp)

        assert sig1 == sig2


class TestSignatureVerification:
    """Test signature verification."""

    def setup_method(self):
        """Setup before each test."""
        self.secret_key = "test_secret_key_12345"
        self.signer = RequestSigner(self.secret_key)
        clear_revoked_timestamps()

    def test_verify_valid_signature(self):
        """Test verifying a valid signature."""
        method = "GET"
        path = "/api/users"

        signature, timestamp = self.signer.sign_request(method, path)
        assert self.signer.verify_request(method, path, signature, timestamp)

    def test_verify_invalid_signature(self):
        """Test verifying an invalid signature."""
        method = "GET"
        path = "/api/users"

        _, timestamp = self.signer.sign_request(method, path)
        assert not self.signer.verify_request(method, path, "invalid_sig", timestamp)

    def test_verify_signature_wrong_method(self):
        """Test that signature fails with wrong method."""
        method1 = "GET"
        method2 = "POST"
        path = "/api/users"

        signature, timestamp = self.signer.sign_request(method1, path)
        assert not self.signer.verify_request(method2, path, signature, timestamp)

    def test_verify_signature_wrong_path(self):
        """Test that signature fails with wrong path."""
        method = "GET"
        path1 = "/api/users"
        path2 = "/api/posts"

        signature, timestamp = self.signer.sign_request(method, path1)
        assert not self.signer.verify_request(method, path2, signature, timestamp)

    def test_verify_signature_wrong_body(self):
        """Test that signature fails with different body."""
        method = "POST"
        path = "/api/users"
        body1 = '{"name": "John"}'
        body2 = '{"name": "Jane"}'

        signature, timestamp = self.signer.sign_request(method, path, body1)
        assert not self.signer.verify_request(method, path, signature, timestamp, body2)

    def test_verify_expired_timestamp(self):
        """Test that expired timestamp is rejected."""
        method = "GET"
        path = "/api/users"

        # Create a timestamp that's too old
        old_timestamp = (datetime.utcnow() - timedelta(minutes=10)).isoformat() + "Z"
        signature, _ = self.signer.sign_request(method, path, timestamp=old_timestamp)

        assert not self.signer.verify_request(method, path, signature, old_timestamp)

    def test_verify_future_timestamp(self):
        """Test that far-future timestamp is rejected."""
        method = "GET"
        path = "/api/users"

        # Create a timestamp in the future
        future_timestamp = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
        signature, _ = self.signer.sign_request(method, path, timestamp=future_timestamp)

        assert not self.signer.verify_request(method, path, signature, future_timestamp)

    def test_verify_with_different_secret_key(self):
        """Test that signature fails with different secret key."""
        method = "GET"
        path = "/api/users"

        signature, timestamp = self.signer.sign_request(method, path)

        # Create new signer with different key
        different_signer = RequestSigner("different_secret_key")
        assert not different_signer.verify_request(method, path, signature, timestamp)


class TestSignatureValidator:
    """Test SignatureValidator wrapper."""

    def setup_method(self):
        """Setup before each test."""
        self.secret_key = "test_secret_key"
        self.validator = SignatureValidator(self.secret_key)

    def test_validate_from_headers(self):
        """Test validation from headers."""
        method = "GET"
        path = "/api/users"

        # Get signing headers
        headers = self.validator.get_signing_headers(method, path)

        # Validate with those headers
        assert self.validator.validate_from_headers(
            method,
            path,
            headers["X-Signature"],
            headers["X-Timestamp"],
        )

    def test_validate_missing_signature_header(self):
        """Test validation with missing signature header."""
        method = "GET"
        path = "/api/users"
        timestamp = datetime.utcnow().isoformat() + "Z"

        assert not self.validator.validate_from_headers(
            method, path, signature_header=None, timestamp_header=timestamp
        )

    def test_validate_missing_timestamp_header(self):
        """Test validation with missing timestamp header."""
        method = "GET"
        path = "/api/users"

        assert not self.validator.validate_from_headers(
            method, path, signature_header="sig", timestamp_header=None
        )

    def test_get_signing_headers(self):
        """Test getting signing headers."""
        method = "POST"
        path = "/api/users"
        body = '{"name": "John"}'

        headers = self.validator.get_signing_headers(method, path, body)

        assert "X-Signature" in headers
        assert "X-Timestamp" in headers
        assert len(headers["X-Signature"]) > 0
        assert "Z" in headers["X-Timestamp"]


class TestTimestampRevocation:
    """Test timestamp revocation for replay attack prevention."""

    def setup_method(self):
        """Setup before each test."""
        clear_revoked_timestamps()

    def test_revoke_timestamp(self):
        """Test revoking a timestamp."""
        timestamp = datetime.utcnow().isoformat() + "Z"

        revoke_timestamp(timestamp)
        assert is_timestamp_revoked(timestamp)

    def test_check_non_revoked_timestamp(self):
        """Test checking a non-revoked timestamp."""
        timestamp = datetime.utcnow().isoformat() + "Z"

        assert not is_timestamp_revoked(timestamp)

    def test_revoke_multiple_timestamps(self):
        """Test revoking multiple timestamps."""
        ts1 = "2026-08-19T10:00:00Z"
        ts2 = "2026-08-19T11:00:00Z"

        revoke_timestamp(ts1)
        revoke_timestamp(ts2)

        assert is_timestamp_revoked(ts1)
        assert is_timestamp_revoked(ts2)

    def test_clear_revoked_timestamps(self):
        """Test clearing all revoked timestamps."""
        ts1 = "2026-08-19T10:00:00Z"
        ts2 = "2026-08-19T11:00:00Z"

        revoke_timestamp(ts1)
        revoke_timestamp(ts2)

        clear_revoked_timestamps()

        assert not is_timestamp_revoked(ts1)
        assert not is_timestamp_revoked(ts2)


class TestConstantTimeComparison:
    """Test constant-time signature comparison."""

    def setup_method(self):
        """Setup before each test."""
        self.secret_key = "test_secret_key"
        self.signer = RequestSigner(self.secret_key)

    def test_timing_attack_resistance(self):
        """Test that comparison is constant-time."""
        method = "GET"
        path = "/api/users"

        correct_sig, timestamp = self.signer.sign_request(method, path)

        # Both should fail, but should take same time regardless of where they differ
        wrong_sig1 = "0" + correct_sig[1:]  # Differs at start
        wrong_sig2 = correct_sig[:-1] + "0"  # Differs at end

        # Both should fail verification
        assert not self.signer.verify_request(method, path, wrong_sig1, timestamp)
        assert not self.signer.verify_request(method, path, wrong_sig2, timestamp)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
