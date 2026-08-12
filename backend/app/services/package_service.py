from __future__ import annotations
"""
app/services/package_service.py — Package CRUD business logic.

All database operations go through this service, keeping routers thin.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.package import Package
from app.schemas.package import PackageCreate, PackageUpdate
from app.utils.id_generator import generate_tracking_id
from typing import Optional, List, Tuple


def create_package(
    db: Session, data: PackageCreate, admin_id: uuid.UUID
) -> Package:
    """Create a new package with a unique tracking ID."""
    tracking_id = generate_tracking_id(db)

    package = Package(
        tracking_id=tracking_id,
        recipient_name=data.recipient_name,
        recipient_email=data.recipient_email.lower(),
        recipient_phone=data.recipient_phone,
        origin=data.origin,
        destination=data.destination,
        description=data.description,
        current_status="Package registered",
        current_location=data.origin,
        created_by=admin_id,

        # Sender / Origin fields
        sender_name=data.sender_name,
        sender_phone=data.sender_phone,
        city_collection=data.city_collection,
        shipping_date=data.shipping_date,
        shipping_quantity=data.shipping_quantity,
        weight_lbs=data.weight_lbs,

        # Recipient / Destination fields
        destination_address=data.destination_address,
        estimated_delivery_date=data.estimated_delivery_date,

        # Geolocation fields
        display_name=data.display_name,
        current_lat=data.current_lat,
        current_lng=data.current_lng,
    )
    db.add(package)
    db.commit()
    db.refresh(package)
    return package


def get_package_by_id(db: Session, package_id: uuid.UUID) -> Optional[Package]:
    """Fetch a single non-deleted package by its internal UUID."""
    return (
        db.query(Package)
        .filter(Package.id == package_id, Package.is_deleted == False)  # noqa: E712
        .first()
    )


def get_package_by_tracking_id(db: Session, tracking_id: str) -> Optional[Package]:
    """Fetch a non-deleted package by its public tracking ID."""
    return (
        db.query(Package)
        .filter(
            Package.tracking_id == tracking_id.upper(),
            Package.is_deleted == False,  # noqa: E712
        )
        .first()
    )


def list_packages(
    db: Session, page: int = 1, page_size: int = 20
) -> Tuple[int, List[Package]]:
    """
    Return paginated list of non-deleted packages (newest first).
    Returns (total_count, items_for_this_page).
    """
    query = (
        db.query(Package)
        .filter(Package.is_deleted == False)  # noqa: E712
        .order_by(Package.created_at.desc())
    )
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, items


def update_package(
    db: Session, package: Package, data: PackageUpdate
) -> Package:
    """
    Apply a partial update (PATCH semantics).
    Only fields explicitly supplied in `data` are changed.
    """
    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(package, field, value)

    package.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(package)
    return package


def soft_delete_package(db: Session, package: Package) -> None:
    """
    Soft-delete: sets is_deleted=True rather than removing the row.
    The tracking record remains queryable for audit purposes.
    """
    package.is_deleted = True
    package.updated_at = datetime.now(timezone.utc)
    db.commit()
