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

    # Sender / Origin
    sender_name: Optional[str] = None
    sender_phone: Optional[str] = None
    sender_address: Optional[str] = None
    city_collection: Optional[str] = None
    shipping_date: Optional[datetime] = None
    shipping_quantity: Optional[int] = None
    weight_lbs: Optional[float] = None
    carrier: Optional[str] = None

    # Recipient / Destination
    delivery_city: Optional[str] = None
    destination_address: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None

    # Geolocation
    display_name: Optional[str] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None


class PackageUpdate(BaseModel):
    """All fields optional — PATCH semantics (only supplied fields are changed)."""
    recipient_name: Optional[str] = None
    recipient_email: Optional[EmailStr] = None
    recipient_phone: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    description: Optional[str] = None
    is_delivered: Optional[bool] = None

    # Sender / Origin
    sender_name: Optional[str] = None
    sender_phone: Optional[str] = None
    sender_address: Optional[str] = None
    city_collection: Optional[str] = None
    shipping_date: Optional[datetime] = None
    shipping_quantity: Optional[int] = None
    weight_lbs: Optional[float] = None
    carrier: Optional[str] = None

    # Recipient / Destination
    delivery_city: Optional[str] = None
    destination_address: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None

    # Geolocation
    display_name: Optional[str] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None


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
    display_name: Optional[str] = None
    is_delivered: bool

    # Sender / Origin
    sender_name: Optional[str]
    sender_phone: Optional[str]
    sender_address: Optional[str]
    city_collection: Optional[str]
    shipping_date: Optional[datetime]
    shipping_quantity: Optional[int]
    weight_lbs: Optional[float]
    carrier: Optional[str]

    # Recipient / Destination
    delivery_city: Optional[str]
    destination_address: Optional[str]
    estimated_delivery_date: Optional[datetime]

    # Geolocation
    display_name: Optional[str] = None
    current_lat: Optional[float]
    current_lng: Optional[float]

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PackageListItem(BaseModel):
    """Abbreviated record for paginated list views."""
    id: uuid.UUID
    tracking_id: str
    recipient_name: str
    recipient_email: str
    destination: Optional[str]
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
