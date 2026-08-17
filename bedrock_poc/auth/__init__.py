"""Authentication module for JWT-based auth and RBAC."""

from bedrock_poc.auth.models import (
    User,
    UserCreate,
    UserLogin,
    UserRole,
    Token,
    TokenPayload,
    TokenRefreshRequest,
    UserResponse,
    PasswordChangeRequest,
    AuthError,
)

from bedrock_poc.auth.auth import (
    AuthService,
    UserService,
)

__all__ = [
    # Models
    "User",
    "UserCreate",
    "UserLogin",
    "UserRole",
    "Token",
    "TokenPayload",
    "TokenRefreshRequest",
    "UserResponse",
    "PasswordChangeRequest",
    "AuthError",
    # Services
    "AuthService",
    "UserService",
]
