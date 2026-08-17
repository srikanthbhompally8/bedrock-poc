"""Authentication models for JWT tokens and user management."""

from enum import Enum
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional


class UserRole(str, Enum):
    """User roles for RBAC (Role-Based Access Control)."""
    ADMIN = "admin"
    RECRUITER = "recruiter"
    CANDIDATE = "candidate"


class User(BaseModel):
    """User model for authentication and authorization."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.CANDIDATE
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(BaseModel):
    """Request model for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.CANDIDATE


class UserLogin(BaseModel):
    """Request model for user login."""
    email: EmailStr
    password: str


class TokenPayload(BaseModel):
    """Payload inside JWT token."""
    user_id: int
    email: EmailStr
    role: UserRole
    exp: datetime = Field(..., description="Token expiration time")
    iat: datetime = Field(default_factory=datetime.utcnow, description="Token issued at")


class Token(BaseModel):
    """Response model for login endpoint."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Seconds until token expires")


class TokenRefreshRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str


class UserResponse(BaseModel):
    """Response model for user endpoints."""
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class PasswordChangeRequest(BaseModel):
    """Request model for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8)


class AuthError(BaseModel):
    """Error response for auth failures."""
    detail: str
    status_code: int
    error_type: str = "auth_error"
