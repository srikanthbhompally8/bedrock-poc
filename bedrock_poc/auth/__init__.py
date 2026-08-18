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

from bedrock_poc.auth.permissions import (
    Permission,
    RolePermissions,
)

from bedrock_poc.auth.authorization import (
    get_current_user,
    get_current_user_full,
    require_role,
    require_permission,
    require_any_permission,
    require_all_permissions,
    has_permission,
    has_any_permission,
    has_all_permissions,
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
    # Permissions
    "Permission",
    "RolePermissions",
    # Authorization
    "get_current_user",
    "get_current_user_full",
    "require_role",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
    "has_permission",
    "has_any_permission",
    "has_all_permissions",
]
