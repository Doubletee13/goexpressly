from __future__ import annotations
"""
app/models/package.py — Shipment/package model.

Stores all package metadata and a denormalised copy of the latest status/location
for fast single-query public lookups without joining tracking_events.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Package(Base):
    __tablename__ = "packages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tracking_id: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )

    # Recipient details — email is used for notifications
    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Shipment metadata
    origin: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    destination: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Sender / Origin details
    sender_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sender_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sender_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city_collection: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    shipping_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    shipping_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weight_lbs: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    carrier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Recipient / Destination details
    delivery_city: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    destination_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Denormalised latest status (updated each time a tracking event is added)
    current_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Geolocation for map display
    current_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Soft-delete flag (keeps the record; excludes from normal queries)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Audit
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("admins.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    created_by_admin = relationship("Admin", back_populates="packages")
    events = relationship(
        "TrackingEvent",
        back_populates="package",
        order_by="TrackingEvent.timestamp.desc()",
        cascade="all, delete-orphan",
    )
    email_logs = relationship(
        "EmailLog", back_populates="package", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Package tracking_id={self.tracking_id} status={self.current_status}>"
