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
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user.

    Args:
        credentials: JWT token from Authorization header

    Returns:
        Current user details

    Raises:
        HTTPException: If token is invalid or expired
    """
    token_payload = AuthService.verify_token(credentials.credentials)

    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = UserService.get_user(token_payload.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at
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
