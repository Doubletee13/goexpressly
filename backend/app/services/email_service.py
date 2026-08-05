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
    logo_url = f"{settings.site_url}/src/assets/logo.png"
    track_url = f"{settings.site_url}/frontend/public/track.html?id={package.tracking_id}"
    return f"""\
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background-color:#f1f5f9;font-family:'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;color:#334155;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f1f5f9;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.08);">

        <!-- ▸ Branded header -->
        <tr>
          <td style="background-color:#0EA5E9;padding:24px 32px;text-align:center;">
            <img src="{logo_url}" alt="GoExpressly" width="180" style="display:block;margin:0 auto;max-width:180px;height:auto;" />
          </td>
        </tr>

        <!-- ▸ Body -->
        <tr>
          <td style="padding:32px;">
            <h2 style="margin:0 0 8px;font-size:18px;font-weight:700;color:#0f172a;">Shipment Update</h2>
            <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.5;">
              Hello {package.recipient_name}, your shipment <strong style="color:#0f172a;">{package.tracking_id}</strong> has a new update.
            </p>

            <!-- Status table -->
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;margin-bottom:24px;">
              <tr style="background-color:#f8fafc;">
                <td style="padding:12px 16px;font-size:13px;font-weight:600;color:#64748b;border-bottom:1px solid #e2e8f0;width:110px;">Status</td>
                <td style="padding:12px 16px;font-size:14px;font-weight:600;color:#0EA5E9;border-bottom:1px solid #e2e8f0;">{event.status_label}</td>
              </tr>
              <tr>
                <td style="padding:12px 16px;font-size:13px;font-weight:600;color:#64748b;border-bottom:1px solid #e2e8f0;width:110px;">Location</td>
                <td style="padding:12px 16px;font-size:14px;color:#334155;border-bottom:1px solid #e2e8f0;">{event.location or 'N/A'}</td>
              </tr>
              <tr style="background-color:#f8fafc;">
                <td style="padding:12px 16px;font-size:13px;font-weight:600;color:#64748b;width:110px;">Time</td>
                <td style="padding:12px 16px;font-size:14px;color:#334155;">{event.timestamp.strftime('%Y-%m-%d %H:%M UTC')}</td>
              </tr>
            </table>

            <!-- CTA button -->
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr><td align="center">
                <a href="{track_url}" style="display:inline-block;background-color:#0EA5E9;color:#ffffff;font-size:14px;font-weight:600;text-decoration:none;padding:12px 28px;border-radius:8px;">
                  Track {package.tracking_id}
                </a>
              </td></tr>
            </table>
          </td>
        </tr>

        <!-- ▸ Footer -->
        <tr>
          <td style="background-color:#f8fafc;padding:20px 32px;border-top:1px solid #e2e8f0;text-align:center;">
            <p style="margin:0 0 4px;font-size:12px;color:#94a3b8;">This is an automated message from GoExpressly. Please do not reply.</p>
            <p style="margin:0;font-size:11px;color:#cbd5e1;">&copy; 2026 GoExpressly. All rights reserved.</p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


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
