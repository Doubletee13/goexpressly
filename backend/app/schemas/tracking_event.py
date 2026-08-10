from __future__ import annotations
"""
app/schemas/tracking_event.py — Pydantic schemas for tracking events.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class EventCreate(BaseModel):
    """Fields required when adding a new tracking event."""
    status_label: str
    location: Optional[str] = None
    notes: Optional[str] = None  # Internal admin notes; not shown publicly
    
    # Optional coordinate updates to move the Google Maps pin
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None


class EventOut(BaseModel):
    """Single tracking event returned to both admin and public views."""
    id: uuid.UUID
    package_id: uuid.UUID
    status_label: str
    location: Optional[str]
    timestamp: datetime

    model_config = {"from_attributes": True}


class EventOutAdmin(EventOut):
    """Extended event view for admins — includes internal notes."""
    notes: Optional[str]

    model_config = {"from_attributes": True}


class PublicTrackingResponse(BaseModel):
    """
    Public tracking lookup response.
    Returns current status, sender/recipient detail, map coords, and ordered history.
    Notes are intentionally excluded.
    """
    tracking_id: str
    recipient_name: str
    origin: Optional[str]
    destination: Optional[str]
    current_status: Optional[str]
    current_location: Optional[str]
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

    # Geolocation for map
    current_lat: Optional[float]
    current_lng: Optional[float]

    history: List[EventOut]

    model_config = {"from_attributes": True}
