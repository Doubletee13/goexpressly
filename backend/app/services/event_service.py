from __future__ import annotations
"""
app/services/event_service.py — Tracking event business logic.

create_event:
  1. Inserts a new TrackingEvent row (history is append-only).
  2. Updates the parent Package's denormalised current_status / current_location
     so public lookups are a single-table query.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.package import Package
from app.models.tracking_event import TrackingEvent
from app.schemas.tracking_event import EventCreate


def create_event(
    db: Session,
    package: Package,
    data: EventCreate,
    admin_id: uuid.UUID,
) -> TrackingEvent:
    """
    Append a new tracking milestone and synchronise the package's denorm fields.
    Returns the freshly-created TrackingEvent (caller triggers email notification).
    """
    event = TrackingEvent(
        package_id=package.id,
        status_label=data.status_label,
        location=data.location,
        notes=data.notes,
        created_by=admin_id,
    )
    db.add(event)

    # Keep denorm fields in sync — these are what the public lookup reads
    package.current_status = data.status_label
    if data.location:
        package.current_location = data.location
        
    if data.current_lat is not None:
        package.current_lat = data.current_lat
    if data.current_lng is not None:
        package.current_lng = data.current_lng

    # Mark as delivered if the status label hints at final delivery
    if _is_delivered_status(data.status_label):
        package.is_delivered = True

    package.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(event)
    return event


def get_events_for_package(
    db: Session, package_id: uuid.UUID
) -> list[TrackingEvent]:
    """
    Return all events for a package, ordered oldest-first
    (good for rendering a timeline from top to bottom).
    """
    return (
        db.query(TrackingEvent)
        .filter(TrackingEvent.package_id == package_id)
        .order_by(TrackingEvent.timestamp.asc())
        .all()
    )


def _is_delivered_status(status_label: str) -> bool:
    """
    Simple heuristic: if admin writes a status containing common delivery
    keywords, mark the package as delivered automatically.
    The admin can also set is_delivered directly via PATCH /packages/{id}.
    """
    keywords = {"delivered", "completed", "collected", "received"}
    return any(kw in status_label.lower() for kw in keywords)
