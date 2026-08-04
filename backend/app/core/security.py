from __future__ import annotations
"""
app/core/security.py — JWT token creation and decoding.

Uses python-jose with HS256 algorithm.
The SECRET_KEY must be a long random string set in .env.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.config import settings


def create_access_token(subject: str) -> str:
    """
    Create a signed JWT for `subject` (admin email).
    Expiry is controlled by ACCESS_TOKEN_EXPIRE_MINUTES from settings.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> Optional[str]:
    """
    Decode a JWT and return the subject (admin email).
    Returns None if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        subject: Optional[str] = payload.get("sub")
        return subject
    except JWTError:
        return None
