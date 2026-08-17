"""JWT authentication logic and user management."""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from passlib.context import CryptContext
from jose import JWTError, jwt
from bedrock_poc.auth.models import (
    User, UserCreate, TokenPayload, Token, UserRole
)

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Move to .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing (using argon2 for better Python 3.12 compatibility)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# In-memory user database (replace with PostgreSQL in production)
users_db = {}
next_user_id = 1


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password from database

        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(
        user_id: int,
        email: str,
        role: UserRole,
        expires_delta: Optional[timedelta] = None
    ) -> Tuple[str, int]:
        """Create a JWT access token.

        Args:
            user_id: User ID to embed in token
            email: User email to embed in token
            role: User role to embed in token
            expires_delta: Custom expiration time (default: 60 minutes)

        Returns:
            Tuple of (token, expires_in_seconds)
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        expire = datetime.utcnow() + expires_delta
        expires_in = int(expires_delta.total_seconds())

        payload = {
            "user_id": user_id,
            "email": email,
            "role": role.value,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt, expires_in

    @staticmethod
    def create_refresh_token(user_id: int, email: str) -> str:
        """Create a JWT refresh token.

        Args:
            user_id: User ID to embed in token
            email: User email to embed in token

        Returns:
            Refresh token
        """
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "user_id": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[TokenPayload]:
        """Verify and decode a JWT token.

        Args:
            token: JWT token to verify

        Returns:
            TokenPayload if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            # Verify token type
            if payload.get("type") != "access":
                return None

            user_id = payload.get("user_id")
            email = payload.get("email")
            role = payload.get("role")

            if user_id is None or email is None or role is None:
                return None

            return TokenPayload(
                user_id=user_id,
                email=email,
                role=UserRole(role),
                exp=datetime.fromtimestamp(payload.get("exp")),
                iat=datetime.fromtimestamp(payload.get("iat"))
            )
        except JWTError:
            return None

    @staticmethod
    def verify_refresh_token(token: str) -> Optional[Tuple[int, str]]:
        """Verify a refresh token and return user info.

        Args:
            token: Refresh token to verify

        Returns:
            Tuple of (user_id, email) if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            # Verify token type
            if payload.get("type") != "refresh":
                return None

            user_id = payload.get("user_id")
            email = payload.get("email")

            if user_id is None or email is None:
                return None

            return (user_id, email)
        except JWTError:
            return None


class UserService:
    """Service for user management operations."""

    @staticmethod
    def register_user(user_create: UserCreate) -> Tuple[User, bool]:
        """Register a new user.

        Args:
            user_create: User creation request

        Returns:
            Tuple of (User object, success boolean)
        """
        global next_user_id

        # Check if user already exists
        for user in users_db.values():
            if user["email"] == user_create.email:
                return None, False

        # Create new user
        user_id = next_user_id
        next_user_id += 1

        hashed_password = AuthService.hash_password(user_create.password)

        user_data = {
            "id": user_id,
            "email": user_create.email,
            "full_name": user_create.full_name,
            "password_hash": hashed_password,
            "role": user_create.role.value,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        users_db[user_id] = user_data

        user = User(
            id=user_id,
            email=user_create.email,
            full_name=user_create.full_name,
            role=user_create.role,
            is_active=True,
            created_at=user_data["created_at"],
            updated_at=user_data["updated_at"]
        )

        return user, True

    @staticmethod
    def login_user(email: str, password: str) -> Optional[Tuple[User, Token]]:
        """Authenticate user and return token.

        Args:
            email: User email
            password: Plain text password

        Returns:
            Tuple of (User, Token) if successful, None if failed
        """
        # Find user by email
        user_data = None
        for user in users_db.values():
            if user["email"] == email:
                user_data = user
                break

        if user_data is None:
            return None

        # Verify password
        if not AuthService.verify_password(password, user_data["password_hash"]):
            return None

        # Create tokens
        access_token, expires_in = AuthService.create_access_token(
            user_id=user_data["id"],
            email=user_data["email"],
            role=UserRole(user_data["role"])
        )

        refresh_token = AuthService.create_refresh_token(
            user_id=user_data["id"],
            email=user_data["email"]
        )

        user = User(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=UserRole(user_data["role"]),
            is_active=user_data["is_active"],
            created_at=user_data["created_at"],
            updated_at=user_data["updated_at"]
        )

        token = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in
        )

        return user, token

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[Token]:
        """Refresh an access token using a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New Token if successful, None if failed
        """
        result = AuthService.verify_refresh_token(refresh_token)

        if result is None:
            return None

        user_id, email = result

        # Find user
        user_data = users_db.get(user_id)
        if user_data is None:
            return None

        # Create new access token
        access_token, expires_in = AuthService.create_access_token(
            user_id=user_id,
            email=email,
            role=UserRole(user_data["role"])
        )

        token = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in
        )

        return token

    @staticmethod
    def get_user(user_id: int) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID to retrieve

        Returns:
            User object if found, None otherwise
        """
        user_data = users_db.get(user_id)

        if user_data is None:
            return None

        return User(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=UserRole(user_data["role"]),
            is_active=user_data["is_active"],
            created_at=user_data["created_at"],
            updated_at=user_data["updated_at"]
        )

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email.

        Args:
            email: User email to search

        Returns:
            User object if found, None otherwise
        """
        for user_data in users_db.values():
            if user_data["email"] == email:
                return User(
                    id=user_data["id"],
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    role=UserRole(user_data["role"]),
                    is_active=user_data["is_active"],
                    created_at=user_data["created_at"],
                    updated_at=user_data["updated_at"]
                )
        return None
