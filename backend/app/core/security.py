"""Security utilities for authentication and authorization."""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    """
    Generate a secure random API key.

    Format: sk_live_<32 random bytes as hex>

    Returns:
        API key string
    """
    prefix = "sk_live" if settings.ENVIRONMENT == "production" else "sk_test"
    random_part = secrets.token_hex(32)
    return f"{prefix}_{random_part}"


def hash_api_key(api_key: str) -> str:
    """
    Hash API key using SHA256.

    Args:
        api_key: Raw API key

    Returns:
        Hashed key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_key_prefix(api_key: str) -> str:
    """
    Extract key prefix for display.

    Args:
        api_key: Raw API key

    Returns:
        First 8 characters
    """
    return api_key[:8]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Token payload
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify JWT token.

    Args:
        token: JWT token

    Returns:
        Token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


async def verify_api_key(
    api_key: str = Security(api_key_header),
    db: AsyncSession = None,
) -> tuple[int, int]:
    """
    Verify API key and return tenant_id and key_id.

    Args:
        api_key: API key from header
        db: Database session

    Returns:
        Tuple of (tenant_id, api_key_id)

    Raises:
        HTTPException: If key is invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Hash the provided key
    key_hash = hash_api_key(api_key)

    # Look up key in database
    from sqlalchemy import select
    from app.models.api_key import APIKey

    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session not available",
        )

    result = await db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
    api_key_obj = result.scalar_one_or_none()

    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not api_key_obj.is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is inactive or expired",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Update last used time
    api_key_obj.last_used_at = datetime.utcnow()
    await db.commit()

    return api_key_obj.tenant_id, api_key_obj.id
