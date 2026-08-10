from __future__ import annotations
"""
app/models/tracking_event.py — Immutable tracking history entry.

Each status/location update creates a NEW row here; nothing is overwritten.
This preserves the full timeline for the public tracking page.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    package_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("packages.id"), nullable=False, index=True
    )

    # Free-text status — no fixed enum; admin writes whatever is accurate
    status_label: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Internal only

    # The authoritative timestamp for this milestone in the journey
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Audit: which admin added this event
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("admins.id"), nullable=False
    )

    # Relationships
    package = relationship("Package", back_populates="events")
    created_by_admin = relationship("Admin", back_populates="tracking_events")
    email_log = relationship(
        "EmailLog", back_populates="tracking_event", uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<TrackingEvent package_id={self.package_id} "
            f"status={self.status_label!r} at={self.timestamp}>"
        )
