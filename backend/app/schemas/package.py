from __future__ import annotations
"""
app/schemas/package.py — Pydantic schemas for package CRUD.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr


# ── Request schemas ────────────────────────────────────────────────────────

class PackageCreate(BaseModel):
    """Fields required when creating a new package."""
    recipient_name: str
    recipient_email: EmailStr
    recipient_phone: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    description: Optional[str] = None


class PackageUpdate(BaseModel):
    """All fields optional — PATCH semantics (only supplied fields are changed)."""
    recipient_name: Optional[str] = None
    recipient_email: Optional[EmailStr] = None
    recipient_phone: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    description: Optional[str] = None
    is_delivered: Optional[bool] = None


# ── Response schemas ────────────────────────────────────────────────────────

class PackageOut(BaseModel):
    """Full package record returned to admin views."""
    id: uuid.UUID
    tracking_id: str
    recipient_name: str
    recipient_email: str
    recipient_phone: Optional[str]
    origin: Optional[str]
    destination: Optional[str]
    description: Optional[str]
    current_status: Optional[str]
    current_location: Optional[str]
    is_delivered: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PackageListItem(BaseModel):
    """Abbreviated record for paginated list views."""
    id: uuid.UUID
    tracking_id: str
    recipient_name: str
    recipient_email: str
    current_status: Optional[str]
    current_location: Optional[str]
    is_delivered: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PackageListResponse(BaseModel):
    """Paginated list wrapper."""
    total: int
    page: int
    page_size: int
    items: List[PackageListItem]
