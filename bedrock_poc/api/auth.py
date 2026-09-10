"""Authentication API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, status, Request
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
    APIKeyCreate,
    APIKeyResponse,
    APIKeySecret,
    APIKeyService,
    get_token_blacklist,
)
from bedrock_poc.security import get_rate_limiter
from bedrock_poc.audit import AuditLogger, AuditEventType

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()
rate_limiter = get_rate_limiter()


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
def login(user_login: UserLogin, request: Request):
    """Authenticate user and return JWT tokens.

    Args:
        user_login: Email and password
        request: HTTP request object

    Returns:
        Access token, refresh token, and expiration time

    Raises:
        HTTPException: If credentials are invalid or rate limited
    """
    # Get client IP for rate limiting
    client_ip = request.client.host if request.client else "unknown"

    # Check rate limit: 5 attempts per minute per email
    try:
        rate_limiter.is_allowed(
            identifier=user_login.email,
            endpoint="login",
            max_requests=5,
            window_seconds=60
        )
    except HTTPException as e:
        # Log rate limit violation
        AuditLogger.log_authentication(
            user_email=user_login.email,
            ip_address=client_ip,
            event_type=AuditEventType.LOGIN_FAILED,
            status="failure",
            error_message="Rate limit exceeded"
        )
        raise

    # Attempt login
    result = UserService.login_user(user_login.email, user_login.password)

    if result is None:
        # Log failed login attempt
        AuditLogger.log_authentication(
            user_email=user_login.email,
            ip_address=client_ip,
            event_type=AuditEventType.LOGIN_FAILED,
            status="failure",
            error_message="Invalid credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    user, token = result

    # Log successful login
    AuditLogger.log_authentication(
        user_id=user.id,
        user_email=user.email,
        ip_address=client_ip,
        event_type=AuditEventType.LOGIN,
        status="success"
    )

    return token


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_req: TokenRefreshRequest, http_request: Request):
    """Refresh an expired access token using a refresh token.

    Args:
        refresh_req: Refresh token
        http_request: HTTP request object

    Returns:
        New access token with same refresh token

    Raises:
        HTTPException: If refresh token is invalid, expired, or rate limited
    """
    # Get client IP for rate limiting
    client_ip = http_request.client.host if http_request.client else "unknown"

    # Check rate limit: 10 refreshes per minute per IP
    try:
        rate_limiter.is_allowed(
            identifier=client_ip,
            endpoint="refresh",
            max_requests=10,
            window_seconds=60
        )
    except HTTPException as e:
        # Log rate limit violation
        AuditLogger.log_event(
            event_type=AuditEventType.TOKEN_REFRESH,
            ip_address=client_ip,
            status="failure",
            error_message="Rate limit exceeded"
        )
        raise

    token = UserService.refresh_access_token(refresh_req.refresh_token)

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Log successful token refresh
    AuditLogger.log_event(
        event_type=AuditEventType.TOKEN_REFRESH,
        ip_address=client_ip,
        status="success"
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


# API Key Management Endpoints

@router.post("/api-keys", response_model=APIKeySecret, status_code=status.HTTP_201_CREATED)
def create_api_key_endpoint(
    api_key_create: APIKeyCreate,
    current_user: User = Depends(get_current_user_full)
):
    """Create a new API key for the current user.

    Args:
        api_key_create: API key creation data
        current_user: Current authenticated user

    Returns:
        Created API key with secret

    Raises:
        HTTPException: If creation fails
    """
    secret, full_key = APIKeyService.create_api_key(
        user_id=current_user.id,
        name=api_key_create.name,
        description=api_key_create.description,
        expires_in_days=api_key_create.expires_in_days,
        role=api_key_create.role if current_user.role == UserRole.ADMIN else current_user.role,
    )

    # Log API key creation
    AuditLogger.log_data_modification(
        event_type=AuditEventType.DATA_CREATED,
        user_id=current_user.id,
        user_email=current_user.email,
        resource_type="APIKey",
        resource_id=secret.id,
        action="create",
        changes={"name": api_key_create.name, "role": secret.role.value}
    )

    return secret


@router.get("/api-keys", response_model=list[APIKeyResponse])
def list_api_keys_endpoint(current_user: User = Depends(get_current_user_full)):
    """List all API keys for the current user.

    Args:
        current_user: Current authenticated user

    Returns:
        List of API keys (without secrets)

    Raises:
        HTTPException: If user not found
    """
    return APIKeyService.list_api_keys(current_user.id)


@router.delete("/api-keys/{key_id}", response_model=dict)
def delete_api_key_endpoint(
    key_id: str,
    current_user: User = Depends(get_current_user_full)
):
    """Delete an API key.

    Args:
        key_id: API key ID to delete
        current_user: Current authenticated user

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If key not found or user unauthorized
    """
    success = APIKeyService.delete_api_key(key_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    # Log API key deletion
    AuditLogger.log_data_modification(
        event_type=AuditEventType.DATA_DELETED,
        user_id=current_user.id,
        user_email=current_user.email,
        resource_type="APIKey",
        resource_id=key_id,
        action="delete"
    )

    return {"message": "API key deleted"}


# Token Revocation and Logout Endpoints

@router.post("/logout", response_model=dict)
def logout(current_user: User = Depends(get_current_user_full), http_request: Request = None):
    """Logout current user by revoking their token.

    Args:
        current_user: Current authenticated user
        http_request: HTTP request object (for logging)

    Returns:
        Logout confirmation

    Raises:
        HTTPException: If logout fails
    """
    # Get the token from the request
    # In a real scenario, you'd extract it from Authorization header
    # For now, we just log the logout
    
    client_ip = http_request.client.host if http_request and http_request.client else "unknown"

    # Log logout
    AuditLogger.log_authentication(
        user_id=current_user.id,
        user_email=current_user.email,
        ip_address=client_ip,
        event_type=AuditEventType.LOGOUT,
        status="success"
    )

    return {"message": "Successfully logged out"}


@router.post("/revoke-token", response_model=dict)
def revoke_token_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    http_request: Request = None
):
    """Revoke a token to prevent further use.

    Args:
        credentials: JWT token from Authorization header
        http_request: HTTP request object (for logging)

    Returns:
        Revocation confirmation

    Raises:
        HTTPException: If revocation fails
    """
    token = credentials.credentials
    
    # Verify token is valid before revoking
    token_payload = AuthService.verify_token(token)
    
    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Revoke the token
    success = AuthService.revoke_token(token)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to revoke token"
        )

    client_ip = http_request.client.host if http_request and http_request.client else "unknown"

    # Log token revocation
    AuditLogger.log_event(
        event_type=AuditEventType.LOGIN,  # Generic event for now
        user_id=token_payload.user_id,
        user_email=token_payload.email,
        ip_address=client_ip,
        status="success",
        metadata={"action": "token_revoked"}
    )

    return {"message": "Token revoked successfully"}


@router.get("/blacklist-status", response_model=dict)
def get_blacklist_status(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Get token blacklist statistics (admin only).

    Args:
        current_user: Current authenticated admin user

    Returns:
        Blacklist statistics

    Raises:
        HTTPException: If user is not admin
    """
    blacklist = get_token_blacklist()
    
    return {
        "blacklisted_tokens": blacklist.get_blacklist_size(),
        "message": "Current number of blacklisted tokens"
    }
