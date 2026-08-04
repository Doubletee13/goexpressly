from __future__ import annotations
"""
app/models/email_log.py — Audit log for every email send attempt.

Written after each attempt (success or failure) so admins can see
delivery status without querying a third-party dashboard.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EmailLog(Base):
    __tablename__ = "email_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    package_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("packages.id"), nullable=False, index=True
    )
    tracking_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tracking_events.id"), nullable=True
    )

    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)

    # "sent" | "failed" | "skipped"
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    package = relationship("Package", back_populates="email_logs")
    tracking_event = relationship("TrackingEvent", back_populates="email_log")

    def __repr__(self) -> str:
        return (
            f"<EmailLog pkg={self.package_id} "
            f"to={self.recipient_email} status={self.status}>"
        )
