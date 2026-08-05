from __future__ import annotations
"""
app/schemas/auth.py — Pydantic schemas for authentication.
"""
from uuid import UUID
from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """Body for POST /api/auth/login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Returned after successful login."""
    access_token: str
    token_type: str = "bearer"


class AdminOut(BaseModel):
    """Safe admin profile — never includes hashed_password."""
    id: UUID
    email: str
    full_name: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}
