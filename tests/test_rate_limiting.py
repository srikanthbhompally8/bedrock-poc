"""Tests for rate limiting functionality."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from bedrock_poc.api.main import app
from bedrock_poc.auth import UserService, UserCreate, UserRole
from bedrock_poc.security import get_rate_limiter

client = TestClient(app)
rate_limiter = get_rate_limiter()


class TestRateLimiter:
    """Test rate limiting functionality."""

    def setup_method(self):
        """Reset rate limiter before each test."""
        rate_limiter.reset()

    def test_rate_limiter_allows_requests_within_limit(self):
        """Test that requests within limit are allowed."""
        identifier = "test_user"
        endpoint = "test_endpoint"

        # First 5 requests should succeed
        for i in range(5):
            rate_limiter.is_allowed(
                identifier=identifier,
                endpoint=endpoint,
                max_requests=5,
                window_seconds=60
            )

    def test_rate_limiter_rejects_requests_over_limit(self):
        """Test that requests exceeding limit are rejected."""
        identifier = "test_user"
        endpoint = "test_endpoint"

        # Make 5 allowed requests
        for i in range(5):
            rate_limiter.is_allowed(
                identifier=identifier,
                endpoint=endpoint,
                max_requests=5,
                window_seconds=60
            )

        # 6th request should be rejected
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            rate_limiter.is_allowed(
                identifier=identifier,
                endpoint=endpoint,
                max_requests=5,
                window_seconds=60
            )
        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_different_identifiers_have_separate_limits(self):
        """Test that different identifiers have separate rate limit counters."""
        endpoint = "test_endpoint"

        # First identifier makes 5 requests
        for i in range(5):
            rate_limiter.is_allowed(
                identifier="user1",
                endpoint=endpoint,
                max_requests=5,
                window_seconds=60
            )

        # Second identifier can still make requests
        rate_limiter.is_allowed(
            identifier="user2",
            endpoint=endpoint,
            max_requests=5,
            window_seconds=60
        )

    def test_different_endpoints_have_separate_limits(self):
        """Test that different endpoints have separate rate limit counters."""
        identifier = "test_user"

        # First endpoint makes 5 requests
        for i in range(5):
            rate_limiter.is_allowed(
                identifier=identifier,
                endpoint="endpoint1",
                max_requests=5,
                window_seconds=60
            )

        # Second endpoint can still make requests
        rate_limiter.is_allowed(
            identifier=identifier,
            endpoint="endpoint2",
            max_requests=5,
            window_seconds=60
        )

    def test_get_remaining_requests(self):
        """Test getting remaining request count."""
        identifier = "test_user"
        endpoint = "test_endpoint"
        max_requests = 5

        # Initially should have 5 remaining
        remaining = rate_limiter.get_remaining_requests(
            identifier=identifier,
            endpoint=endpoint,
            max_requests=max_requests,
            window_seconds=60
        )
        assert remaining == 5

        # Make 2 requests
        for i in range(2):
            rate_limiter.is_allowed(
                identifier=identifier,
                endpoint=endpoint,
                max_requests=max_requests,
                window_seconds=60
            )

        # Should have 3 remaining
        remaining = rate_limiter.get_remaining_requests(
            identifier=identifier,
            endpoint=endpoint,
            max_requests=max_requests,
            window_seconds=60
        )
        assert remaining == 3

    def test_reset_rate_limit_all(self):
        """Test resetting all rate limits."""
        identifier = "test_user"
        endpoint = "test_endpoint"

        # Make 5 requests (hit limit)
        for i in range(5):
            rate_limiter.is_allowed(
                identifier=identifier,
                endpoint=endpoint,
                max_requests=5,
                window_seconds=60
            )

        # Reset all
        rate_limiter.reset()

        # Should be able to make requests again
        rate_limiter.is_allowed(
            identifier=identifier,
            endpoint=endpoint,
            max_requests=5,
            window_seconds=60
        )

    def test_reset_rate_limit_specific_identifier(self):
        """Test resetting rate limit for specific identifier."""
        endpoint = "test_endpoint"

        # Make requests for two identifiers
        for i in range(5):
            rate_limiter.is_allowed(
                identifier="user1",
                endpoint=endpoint,
                max_requests=5,
                window_seconds=60
            )

        for i in range(3):
            rate_limiter.is_allowed(
                identifier="user2",
                endpoint=endpoint,
                max_requests=5,
                window_seconds=60
            )

        # Reset user1
        rate_limiter.reset(identifier="user1", endpoint=endpoint)

        # user1 should be able to make requests
        rate_limiter.is_allowed(
            identifier="user1",
            endpoint=endpoint,
            max_requests=5,
            window_seconds=60
        )

        # user2 should still be limited
        from fastapi import HTTPException
        for i in range(2):
            rate_limiter.is_allowed(
                identifier="user2",
                endpoint=endpoint,
                max_requests=5,
                window_seconds=60
            )

        with pytest.raises(HTTPException):
            rate_limiter.is_allowed(
                identifier="user2",
                endpoint=endpoint,
                max_requests=5,
                window_seconds=60
            )


class TestAuthenticationRateLimiting:
    """Test rate limiting on authentication endpoints."""

    def setup_method(self):
        """Setup test environment."""
        rate_limiter.reset()
        # Create test user
        user_create = UserCreate(
            email="rate_limit_test@example.com",
            password="testpass123",
            full_name="Test User",
            role=UserRole.CANDIDATE
        )
        try:
            UserService.register_user(user_create)
        except:
            pass  # User might already exist

    def test_login_rate_limiting(self):
        """Test rate limiting on login endpoint."""
        email = "rate_limit_test@example.com"

        # First 5 failed login attempts should be allowed
        for i in range(5):
            response = client.post(
                "/api/auth/login",
                json={"email": email, "password": "wrongpassword"}
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # 6th attempt should be rate limited
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": "wrongpassword"}
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_successful_login_counts_against_rate_limit(self):
        """Test that successful login also counts against rate limit."""
        email = "rate_limit_test@example.com"
        password = "testpass123"

        # Make 5 login attempts (mix of failed and successful)
        for i in range(4):
            response = client.post(
                "/api/auth/login",
                json={"email": email, "password": "wrongpassword"}
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # 5th attempt is successful
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": password}
        )
        assert response.status_code == status.HTTP_200_OK

        # 6th attempt should be rate limited
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": password}
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_token_refresh_rate_limiting(self):
        """Test rate limiting on token refresh endpoint."""
        email = "rate_limit_test@example.com"
        password = "testpass123"

        # Get valid token
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": password}
        )
        assert response.status_code == status.HTTP_200_OK
        token_data = response.json()
        refresh_token = token_data["refresh_token"]

        # Reset rate limiter to allow more requests per minute
        rate_limiter.reset()

        # Make 10 token refresh requests (should succeed)
        for i in range(10):
            response = client.post(
                "/api/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            # Might get 401 if token is invalid but not 429
            if response.status_code != status.HTTP_401_UNAUTHORIZED:
                assert response.status_code == status.HTTP_200_OK

        # 11th request should be rate limited (limit is 10 per minute)
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
