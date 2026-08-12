from __future__ import annotations
"""
app/routers/tracking.py — Public unauthenticated tracking lookup.

GET /api/track/{tracking_id}

No authentication required. Returns the package's public info and
full event history (oldest-first for timeline display). Internal
admin notes are intentionally excluded from this response.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.tracking_event import EventOut, PublicTrackingResponse
from app.services import event_service, package_service

router = APIRouter(prefix="/api/track", tags=["Public Tracking"])


@router.get(
    "/{tracking_id}",
    response_model=PublicTrackingResponse,
    summary="Track a package (public)",
    description=(
        "Unauthenticated endpoint. Returns the current status and full tracking "
        "history for a given tracking ID. Admin-only notes are excluded. "
        "Returns 404 if the tracking ID does not exist or has been deleted."
    ),
)
def track_package(
    tracking_id: str,
    db: Session = Depends(get_db),
) -> PublicTrackingResponse:
    package = package_service.get_package_by_tracking_id(db, tracking_id)
    if not package:
        raise HTTPException(
            status_code=404,
            detail=f"No shipment found for tracking ID '{tracking_id.upper()}'",
        )

    events = event_service.get_events_for_package(db, package_id=package.id)

    return PublicTrackingResponse(
        tracking_id=package.tracking_id,
        recipient_name=package.recipient_name,
        origin=package.origin,
        destination=package.destination,
        current_status=package.current_status,
        current_location=package.current_location,
        display_name=package.display_name,
        is_delivered=package.is_delivered,
        # Sender / Origin
        sender_name=package.sender_name,
        sender_phone=package.sender_phone,
        city_collection=package.city_collection,
        shipping_date=package.shipping_date,
        shipping_quantity=package.shipping_quantity,
        weight_lbs=package.weight_lbs,
        # Recipient / Destination
        destination_address=package.destination_address,
        estimated_delivery_date=package.estimated_delivery_date,
        # Geolocation
        current_lat=package.current_lat,
        current_lng=package.current_lng,
        history=[EventOut.model_validate(e) for e in events],
    )
