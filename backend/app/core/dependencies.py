from __future__ import annotations
"""
app/core/dependencies.py — Shared FastAPI dependency functions.

get_db:           yields a SQLAlchemy session; always closed after request.
get_current_admin: decodes JWT, fetches admin from DB, raises 401 if invalid.
"""
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import SessionLocal
from app.models.admin import Admin

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_db() -> Generator[Session, None, None]:
    """Dependency: yields a DB session for the duration of a request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Admin:
    """
    Dependency: validates the Bearer JWT and returns the Admin ORM object.
    Raises HTTP 401 if the token is missing, invalid, expired, or the admin
    no longer exists / is deactivated.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = decode_access_token(token)
    if not email:
        raise credentials_exception

    admin = db.query(Admin).filter(Admin.email == email).first()
    if admin is None or not admin.is_active:
        raise credentials_exception

    return admin
