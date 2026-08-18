"""Authentication API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bedrock_poc.auth import (
    UserService,
    AuthService,
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
    TokenRefreshRequest,
    User,
    UserRole,
    get_current_user,
    get_current_user_full,
    require_role,
    require_permission,
    Permission,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_create: UserCreate):
    """Register a new user.

    Args:
        user_create: User registration data (email, password, full_name, role)

    Returns:
        Created user details (no password)

    Raises:
        HTTPException: If user already exists
    """
    user, success = UserService.register_user(user_create)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at
    )


@router.post("/login", response_model=Token)
def login(user_login: UserLogin):
    """Authenticate user and return JWT tokens.

    Args:
        user_login: Email and password

    Returns:
        Access token, refresh token, and expiration time

    Raises:
        HTTPException: If credentials are invalid
    """
    result = UserService.login_user(user_login.email, user_login.password)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    user, token = result

    return token


@router.post("/refresh", response_model=Token)
def refresh_token(request: TokenRefreshRequest):
    """Refresh an expired access token using a refresh token.

    Args:
        request: Refresh token

    Returns:
        New access token with same refresh token

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    token = UserService.refresh_access_token(request.refresh_token)

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    return token


@router.get("/me", response_model=UserResponse)
def get_current_user_endpoint(current_user: User = Depends(get_current_user_full)):
    """Get current authenticated user.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user details

    Raises:
        HTTPException: If token is invalid or expired
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.post("/verify-token")
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify if a token is valid.

    Args:
        credentials: JWT token from Authorization header

    Returns:
        Token validity status and user info

    Raises:
        HTTPException: If token is invalid
    """
    token_payload = AuthService.verify_token(credentials.credentials)

    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return {
        "valid": True,
        "user_id": token_payload.user_id,
        "email": token_payload.email,
        "role": token_payload.role.value,
        "expires_at": token_payload.exp.isoformat()
    }


@router.get("/users", response_model=list[UserResponse])
def list_users(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """List all users (admin only).

    Args:
        current_user: Current authenticated admin user

    Returns:
        List of all users

    Raises:
        HTTPException: If user is not an admin
    """
    from bedrock_poc.auth.auth import users_db

    users = []
    for user_data in users_db.values():
        users.append(UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=UserRole(user_data["role"]),
            is_active=user_data["is_active"],
            created_at=user_data["created_at"]
        ))
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user_full)
):
    """Get user details.

    Args:
        user_id: User ID to retrieve
        current_user: Current authenticated user

    Returns:
        User details

    Raises:
        HTTPException: If user not found or no permission
    """
    user = UserService.get_user(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view other users' profiles"
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at
    )
