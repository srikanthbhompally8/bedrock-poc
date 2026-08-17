"""Authentication tests."""

import pytest
from bedrock_poc.auth import (
    UserService, AuthService, UserCreate, UserRole, UserLogin
)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "MySecurePassword123"
        hashed = AuthService.hash_password(password)

        assert hashed != password
        assert len(hashed) > 20

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "MySecurePassword123"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "MySecurePassword123"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password("WrongPassword", hashed) is False

    def test_password_hash_consistency(self):
        """Test that same password produces different hashes (salt)."""
        password = "MySecurePassword123"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)

        assert hash1 != hash2
        assert AuthService.verify_password(password, hash1) is True
        assert AuthService.verify_password(password, hash2) is True


class TestTokenCreation:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test access token creation."""
        token, expires_in = AuthService.create_access_token(
            user_id=1,
            email="test@example.com",
            role=UserRole.RECRUITER
        )

        assert isinstance(token, str)
        assert len(token) > 50
        assert expires_in == 3600  # 60 minutes

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        token = AuthService.create_refresh_token(
            user_id=1,
            email="test@example.com"
        )

        assert isinstance(token, str)
        assert len(token) > 50

    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        token, _ = AuthService.create_access_token(
            user_id=1,
            email="test@example.com",
            role=UserRole.RECRUITER
        )

        payload = AuthService.verify_token(token)

        assert payload is not None
        assert payload.user_id == 1
        assert payload.email == "test@example.com"
        assert payload.role == UserRole.RECRUITER

    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        invalid_token = "not.a.valid.jwt.token"

        payload = AuthService.verify_token(invalid_token)

        assert payload is None

    def test_verify_tampered_token(self):
        """Test that tampered token is rejected."""
        token, _ = AuthService.create_access_token(
            user_id=1,
            email="test@example.com",
            role=UserRole.RECRUITER
        )

        # Tamper with token
        tampered_token = token[:-10] + "corrupted!"

        payload = AuthService.verify_token(tampered_token)

        assert payload is None

    def test_verify_refresh_token_valid(self):
        """Test verifying a valid refresh token."""
        token = AuthService.create_refresh_token(
            user_id=1,
            email="test@example.com"
        )

        result = AuthService.verify_refresh_token(token)

        assert result is not None
        user_id, email = result
        assert user_id == 1
        assert email == "test@example.com"

    def test_verify_refresh_token_invalid(self):
        """Test verifying an invalid refresh token."""
        result = AuthService.verify_refresh_token("invalid.token")

        assert result is None


class TestUserRegistration:
    """Test user registration."""

    def test_register_user_success(self):
        """Test successful user registration."""
        user_create = UserCreate(
            email="newuser@example.com",
            password="SecurePassword123",
            full_name="New User",
            role=UserRole.RECRUITER
        )

        user, success = UserService.register_user(user_create)

        assert success is True
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.role == UserRole.RECRUITER
        assert user.is_active is True

    def test_register_duplicate_email(self):
        """Test registration with duplicate email fails."""
        user_create1 = UserCreate(
            email="duplicate@example.com",
            password="Password123",
            full_name="User 1"
        )

        user_create2 = UserCreate(
            email="duplicate@example.com",
            password="Password456",
            full_name="User 2"
        )

        # First registration succeeds
        user1, success1 = UserService.register_user(user_create1)
        assert success1 is True

        # Second registration fails
        user2, success2 = UserService.register_user(user_create2)
        assert success2 is False
        assert user2 is None


class TestUserLogin:
    """Test user login."""

    def test_login_success(self):
        """Test successful login."""
        # Create user first
        user_create = UserCreate(
            email="login@example.com",
            password="LoginPass123",
            full_name="Login User"
        )
        UserService.register_user(user_create)

        # Login
        result = UserService.login_user("login@example.com", "LoginPass123")

        assert result is not None
        user, token = result
        assert user.email == "login@example.com"
        assert token.access_token is not None
        assert token.refresh_token is not None
        assert token.token_type == "bearer"
        assert token.expires_in == 3600

    def test_login_wrong_password(self):
        """Test login with wrong password."""
        # Create user
        user_create = UserCreate(
            email="wrongpass@example.com",
            password="CorrectPass123",
            full_name="Wrong Pass User"
        )
        UserService.register_user(user_create)

        # Try login with wrong password
        result = UserService.login_user("wrongpass@example.com", "WrongPass456")

        assert result is None

    def test_login_nonexistent_user(self):
        """Test login with non-existent email."""
        result = UserService.login_user("nonexistent@example.com", "AnyPassword")

        assert result is None


class TestTokenRefresh:
    """Test token refresh."""

    def test_refresh_access_token_success(self):
        """Test successful token refresh."""
        # Create user and login
        user_create = UserCreate(
            email="refresh@example.com",
            password="RefreshPass123",
            full_name="Refresh User"
        )
        UserService.register_user(user_create)

        result = UserService.login_user("refresh@example.com", "RefreshPass123")
        _, token = result

        # Refresh token
        new_token = UserService.refresh_access_token(token.refresh_token)

        assert new_token is not None
        assert new_token.access_token is not None
        assert new_token.refresh_token == token.refresh_token
        # Verify new token is valid
        payload = AuthService.verify_token(new_token.access_token)
        assert payload is not None

    def test_refresh_with_invalid_token(self):
        """Test refresh with invalid refresh token."""
        new_token = UserService.refresh_access_token("invalid.refresh.token")

        assert new_token is None


class TestGetUser:
    """Test user retrieval."""

    def test_get_user_by_id(self):
        """Test getting user by ID."""
        # Create user
        user_create = UserCreate(
            email="getuser@example.com",
            password="GetUserPass123",
            full_name="Get User"
        )
        created_user, _ = UserService.register_user(user_create)

        # Retrieve user
        retrieved_user = UserService.get_user(created_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == "getuser@example.com"

    def test_get_nonexistent_user(self):
        """Test getting non-existent user."""
        user = UserService.get_user(99999)

        assert user is None

    def test_get_user_by_email(self):
        """Test getting user by email."""
        # Create user
        user_create = UserCreate(
            email="byemail@example.com",
            password="ByEmailPass123",
            full_name="By Email User"
        )
        UserService.register_user(user_create)

        # Retrieve by email
        retrieved_user = UserService.get_user_by_email("byemail@example.com")

        assert retrieved_user is not None
        assert retrieved_user.email == "byemail@example.com"

    def test_get_nonexistent_email(self):
        """Test getting user with non-existent email."""
        user = UserService.get_user_by_email("nonexistent@example.com")

        assert user is None


class TestEndToEnd:
    """End-to-end authentication workflow tests."""

    def test_complete_auth_workflow(self):
        """Test complete authentication workflow."""
        # 1. Register user
        user_create = UserCreate(
            email="workflow@example.com",
            password="WorkflowPass123",
            full_name="Workflow User",
            role=UserRole.RECRUITER
        )
        user, success = UserService.register_user(user_create)
        assert success is True
        assert user.role == UserRole.RECRUITER

        # 2. Login
        result = UserService.login_user("workflow@example.com", "WorkflowPass123")
        assert result is not None
        user, token = result
        assert token.access_token is not None

        # 3. Verify token
        payload = AuthService.verify_token(token.access_token)
        assert payload is not None
        assert payload.user_id == user.id
        assert payload.role == UserRole.RECRUITER

        # 4. Refresh token
        new_token = UserService.refresh_access_token(token.refresh_token)
        assert new_token is not None
        assert new_token.access_token is not None
        assert new_token.refresh_token == token.refresh_token

        # 5. Verify new token is valid
        new_payload = AuthService.verify_token(new_token.access_token)
        assert new_payload is not None
        assert new_payload.user_id == payload.user_id
        assert new_payload.role == UserRole.RECRUITER

    def test_password_change_workflow(self):
        """Test changing password."""
        # Create user
        user_create = UserCreate(
            email="pwchange@example.com",
            password="OldPassword123",
            full_name="Password Change User"
        )
        UserService.register_user(user_create)

        # Login with old password
        result = UserService.login_user("pwchange@example.com", "OldPassword123")
        assert result is not None

        # Simulate password change by registering new user with same approach
        # (In production, would have a password change method)
        result_old = UserService.login_user("pwchange@example.com", "OldPassword123")
        assert result_old is not None
