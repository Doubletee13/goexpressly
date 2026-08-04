from __future__ import annotations
"""
app/services/email_service.py — Email notification dispatcher.

Supports two providers controlled by the EMAIL_PROVIDER env var:
  - "smtp"   → standard SMTP (use Mailtrap sandbox in dev, any SMTP in prod)
  - "resend" → Resend REST API (recommended for production)

Called as a FastAPI BackgroundTask so it never blocks the HTTP response.
Every send attempt (success or failure) is written to the email_logs table.
"""
import smtplib
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.config import settings
from app.models.email_log import EmailLog
from app.models.package import Package
from app.models.tracking_event import TrackingEvent
from app.database import SessionLocal


# ── Email body composers ───────────────────────────────────────────────────

def _build_subject(package: Package, event: TrackingEvent) -> str:
    return f"[GoExpressly] Update for your shipment {package.tracking_id}"


def _build_html_body(package: Package, event: TrackingEvent) -> str:
    return f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
      <h2 style="color: #1a56db;">GoExpressly — Shipment Update</h2>
      <p>Hello {package.recipient_name},</p>
      <p>Your shipment <strong>{package.tracking_id}</strong> has been updated:</p>
      <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
        <tr>
          <td style="padding: 8px; border: 1px solid #ddd;"><strong>Status</strong></td>
          <td style="padding: 8px; border: 1px solid #ddd;">{event.status_label}</td>
        </tr>
        <tr>
          <td style="padding: 8px; border: 1px solid #ddd;"><strong>Location</strong></td>
          <td style="padding: 8px; border: 1px solid #ddd;">{event.location or 'N/A'}</td>
        </tr>
        <tr>
          <td style="padding: 8px; border: 1px solid #ddd;"><strong>Time</strong></td>
          <td style="padding: 8px; border: 1px solid #ddd;">{event.timestamp.strftime('%Y-%m-%d %H:%M UTC')}</td>
        </tr>
      </table>
      <p style="margin-top: 16px;">
        Use your tracking ID <strong>{package.tracking_id}</strong> to check
        the full history on our tracking portal.
      </p>
      <p style="color: #999; font-size: 12px; margin-top: 24px;">
        This is an automated message. Please do not reply.
      </p>
    </body></html>
    """


def _build_text_body(package: Package, event: TrackingEvent) -> str:
    return (
        f"GoExpressly Shipment Update\n\n"
        f"Hello {package.recipient_name},\n\n"
        f"Tracking ID: {package.tracking_id}\n"
        f"Status: {event.status_label}\n"
        f"Location: {event.location or 'N/A'}\n"
        f"Time: {event.timestamp.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"This is an automated message. Please do not reply."
    )


# ── Delivery drivers ───────────────────────────────────────────────────────

def _send_via_smtp(to_email: str, subject: str, html: str, text: str) -> None:
    """Send via SMTP (Mailtrap in dev, any SMTP relay in prod)."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.from_email
    msg["To"] = to_email
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.from_email, to_email, msg.as_string())


def _send_via_resend(to_email: str, subject: str, html: str) -> None:
    """Send via Resend REST API (production)."""
    import resend  # lazy import — only needed when EMAIL_PROVIDER=resend

    resend.api_key = settings.resend_api_key
    resend.Emails.send(
        {
            "from": settings.from_email,
            "to": [to_email],
            "subject": subject,
            "html": html,
        }
    )


# ── Public entry point (called by BackgroundTask) ─────────────────────────

def send_update_email(
    package_id: uuid.UUID,
    event_id: uuid.UUID,
) -> None:
    """
    Compose and send a notification email for a new tracking event.
    Writes an EmailLog row regardless of success or failure.

    Instantiates a fresh database session since this runs as a BackgroundTask
    after the HTTP response (and its DB session) has already closed.
    """
    db = SessionLocal()
    try:
        package = db.query(Package).get(package_id)
        event = db.query(TrackingEvent).get(event_id)
        
        if not package or not event:
            print(f"[email_service] Missing package {package_id} or event {event_id}")
            return

        subject = _build_subject(package, event)
        html = _build_html_body(package, event)
        text = _build_text_body(package, event)
        to_email = package.recipient_email

        log_status = "failed"
        error_detail = None

        try:
            provider = settings.email_provider.lower()
            if provider == "resend":
                _send_via_resend(to_email, subject, html)
            elif provider == "smtp":
                _send_via_smtp(to_email, subject, html, text)
            else:
                raise ValueError(f"Unknown email provider: '{provider}'")

            log_status = "sent"

        except Exception as exc:  # noqa: BLE001
            error_detail = str(exc)
            # Do NOT re-raise — email failure must never break the API response
            print(f"[email_service] Failed to send email to {to_email}: {exc}")

        finally:
            try:
                log = EmailLog(
                    package_id=package.id,
                    tracking_event_id=event.id,
                    recipient_email=to_email,
                    subject=subject,
                    status=log_status,
                    error_detail=error_detail,
                )
                db.add(log)
                db.commit()
            except Exception as log_exc:
                print(f"[email_service] Failed to write EmailLog: {log_exc}")

    finally:
        db.close()
