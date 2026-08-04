from __future__ import annotations
"""
app/routers/auth.py — Admin authentication endpoints.

POST /api/auth/login  — accepts email + password, returns JWT
GET  /api/auth/me     — returns the current admin's profile (JWT required)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_admin
from app.core.security import create_access_token
from app.models.admin import Admin
from app.schemas.auth import AdminOut, LoginRequest, TokenResponse
from app.services.auth_service import authenticate_admin

router = APIRouter(prefix="/api/auth", tags=["Auth"])


from fastapi.security import OAuth2PasswordRequestForm
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Admin login",
    description=(
        "Accepts email (as username) and password in OAuth2 form format. Returns a signed JWT on success."
    ),
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
) -> TokenResponse:
    admin = authenticate_admin(db, email=form_data.username, password=form_data.password)
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=admin.email)
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=AdminOut,
    summary="Get current admin profile",
)
def get_me(current_admin: Admin = Depends(get_current_admin)) -> AdminOut:
    return AdminOut.model_validate(current_admin)
