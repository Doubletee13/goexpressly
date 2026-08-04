from __future__ import annotations
"""
app/services/auth_service.py — Password hashing and login verification.

Uses bcrypt directly (no passlib wrapper) as specified.
  - hash_password:   called by scripts/seed_admin.py and any future admin creation
  - verify_password: called by the login endpoint
  - authenticate_admin: full login flow returning the Admin ORM object or None
"""
import bcrypt
from sqlalchemy.orm import Session

from app.models.admin import Admin
from typing import Optional


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password with bcrypt (12 rounds).
    Returns the hash as a UTF-8 string ready for DB storage.
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Safely compare a plain-text password against its bcrypt hash.
    bcrypt.checkpw is constant-time — no timing attack surface.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def authenticate_admin(db: Session, email: str, password: str) -> Optional[Admin]:
    """
    Look up an admin by email and verify the supplied password.
    Returns the Admin ORM object on success, None on any failure.
    Always performs a bcrypt check even when the user doesn't exist,
    to prevent user-enumeration via timing differences.
    """
    admin = db.query(Admin).filter(Admin.email == email.lower()).first()

    # Always run bcrypt to neutralise timing-based user enumeration
    dummy_hash = "$2b$12$invalidhashpaddingtomakeitlongenoughXXXXXXXXXXXXXXXXXXX"
    check_hash = admin.hashed_password if admin else dummy_hash

    if not verify_password(password, check_hash):
        return None

    if admin and not admin.is_active:
        return None

    return admin
