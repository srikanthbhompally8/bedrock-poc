"""Authorization middleware and decorators for RBAC."""

from functools import wraps
from typing import Callable, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from bedrock_poc.auth.models import User, UserRole, TokenPayload
from bedrock_poc.auth.auth import AuthService, UserService
from bedrock_poc.auth.permissions import Permission, RolePermissions


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    """Extract and verify current user from JWT token.

    Args:
        credentials: HTTP Bearer credentials from Authorization header

    Returns:
        TokenPayload with user information

    Raises:
        HTTPException: If token is invalid, expired, or missing
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_payload = AuthService.verify_token(credentials.credentials)

    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_payload


def get_current_user_full(
    token_payload: TokenPayload = Depends(get_current_user),
) -> User:
    """Get full User object for current authenticated user.

    Args:
        token_payload: Token payload from get_current_user dependency

    Returns:
        Full User object

    Raises:
        HTTPException: If user not found
    """
    user = UserService.get_user(token_payload.user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or inactive",
        )

    return user


def require_role(*roles: UserRole) -> Callable:
    """Decorator to require specific roles for an endpoint.

    Args:
        roles: Required user roles

    Returns:
        Dependency function

    Example:
        @app.get("/admin-only")
        def admin_endpoint(
            current_user: User = Depends(require_role(UserRole.ADMIN))
        ):
            return {"message": "Admin only"}
    """

    async def check_role(user: User = Depends(get_current_user_full)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires one of these roles: {', '.join(r.value for r in roles)}",
            )
        return user

    return check_role


def require_permission(*permissions: Permission) -> Callable:
    """Decorator to require specific permissions for an endpoint.

    Args:
        permissions: Required permissions

    Returns:
        Dependency function

    Example:
        @app.post("/create-job")
        def create_job(
            current_user: User = Depends(require_permission(Permission.CREATE_JOB))
        ):
            return {"message": "Job created"}
    """

    async def check_permission(user: User = Depends(get_current_user_full)) -> User:
        user_permissions = RolePermissions.get_permissions(user.role)

        has_permission = any(perm in user_permissions for perm in permissions)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(p.value for p in permissions)}",
            )
        return user

    return check_permission


def require_any_permission(*permissions: Permission) -> Callable:
    """Decorator to require any of the specified permissions.

    Args:
        permissions: Required permissions (any one of them)

    Returns:
        Dependency function
    """

    async def check_permission(user: User = Depends(get_current_user_full)) -> User:
        if not RolePermissions.has_any_permission(user.role, list(permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(p.value for p in permissions)}",
            )
        return user

    return check_permission


def require_all_permissions(*permissions: Permission) -> Callable:
    """Decorator to require all specified permissions.

    Args:
        permissions: Required permissions (all of them)

    Returns:
        Dependency function
    """

    async def check_permission(user: User = Depends(get_current_user_full)) -> User:
        if not RolePermissions.has_all_permissions(user.role, list(permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(p.value for p in permissions)}",
            )
        return user

    return check_permission


def has_permission(user: User, permission: Permission) -> bool:
    """Check if user has a specific permission.

    Args:
        user: User to check
        permission: Permission to verify

    Returns:
        True if user has the permission, False otherwise
    """
    return RolePermissions.has_permission(user.role, permission)


def has_any_permission(user: User, permissions: List[Permission]) -> bool:
    """Check if user has any of the specified permissions.

    Args:
        user: User to check
        permissions: Permissions to verify

    Returns:
        True if user has any permission, False otherwise
    """
    return RolePermissions.has_any_permission(user.role, permissions)


def has_all_permissions(user: User, permissions: List[Permission]) -> bool:
    """Check if user has all specified permissions.

    Args:
        user: User to check
        permissions: Permissions to verify

    Returns:
        True if user has all permissions, False otherwise
    """
    return RolePermissions.has_all_permissions(user.role, permissions)
