from __future__ import annotations
"""
app/routers/events.py — Tracking event endpoints (admin-only).

POST /api/packages/{package_id}/events  — add a new tracking milestone
GET  /api/packages/{package_id}/events  — list all events for a package

Email notification is triggered as a BackgroundTask after event creation so
the API response is returned immediately without blocking on the email send.
"""
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin, get_db
from app.models.admin import Admin
from app.schemas.tracking_event import EventCreate, EventOutAdmin
from typing import List
from app.services import event_service, package_service
from app.services.email_service import send_update_email

router = APIRouter(prefix="/api/packages", tags=["Tracking Events"])


@router.post(
    "/{package_id}/events",
    response_model=EventOutAdmin,
    status_code=status.HTTP_201_CREATED,
    summary="Add a tracking event (admin)",
    description=(
        "Appends a new status/location milestone to the package history. "
        "The package's current_status and current_location are updated immediately. "
        "An email notification is dispatched to the recipient in the background."
    ),
)
def add_event(
    package_id: uuid.UUID,
    body: EventCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
) -> EventOutAdmin:
    package = package_service.get_package_by_id(db, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    event = event_service.create_event(
        db, package=package, data=body, admin_id=current_admin.id
    )

    # Non-blocking: email sent after response is returned to the client
    background_tasks.add_task(send_update_email, package_id=package.id, event_id=event.id)

    return EventOutAdmin.model_validate(event)


@router.get(
    "/{package_id}/events",
    response_model=List[EventOutAdmin],
    summary="List tracking events for a package (admin)",
)
def list_events(
    package_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> list[EventOutAdmin]:
    package = package_service.get_package_by_id(db, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    events = event_service.get_events_for_package(db, package_id=package.id)
    return [EventOutAdmin.model_validate(e) for e in events]
