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
    Returns current status, destination, and ordered history.
    Notes are intentionally excluded.
    """
    tracking_id: str
    recipient_name: str
    origin: Optional[str]
    destination: Optional[str]
    current_status: Optional[str]
    current_location: Optional[str]
    is_delivered: bool
    history: List[EventOut]

    model_config = {"from_attributes": True}
