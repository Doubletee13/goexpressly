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

def _get_track_url(tracking_id: str) -> str:
    """Generate canonical public tracking URL with pre-filled tracking ID."""
    base = settings.site_url.rstrip('/')
    return f"{base}/track?id={tracking_id}"


def _get_branded_header_html() -> str:
    """Return email-safe branded header with inline vector logo (dark navy background)."""
    return """\
<tr style="background-color:#0f172a;">
  <td style="padding:28px 32px;text-align:center;border-bottom:3px solid #0EA5E9;">
    <!-- Inline SVG Logo -->
    <svg xmlns="http://www.w3.org/2000/svg" width="220" height="42" viewBox="0 0 240 48" fill="none" style="display:inline-block;margin:0 auto;vertical-align:middle;">
      <g transform="translate(4, 9)">
        <path fill="#38BDF8" d="M8 0 L32 15 L8 30 L15 15 Z" />
        <path fill="#BAE6FD" d="M0 0 L24 15 L0 30 L7 15 Z" opacity="0.8"/>
      </g>
      <text x="46" y="32" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">
        <tspan fill="#FFFFFF" font-weight="800" font-size="26px" letter-spacing="-0.5px">Go</tspan>
        <tspan fill="#7DD3FC" font-weight="300" font-size="26px" letter-spacing="-0.2px">Expressly</tspan>
      </text>
    </svg>
  </td>
</tr>"""


def _build_creation_subject(package: Package) -> str:
    return f"[GoExpressly] Your shipment {package.tracking_id} has been registered"


def _build_creation_html(package: Package) -> str:
    track_url = _get_track_url(package.tracking_id)
    header_html = _get_branded_header_html()
    est_date = package.estimated_delivery_date.strftime('%d %b %Y') if package.estimated_delivery_date else 'Pending'

    return f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#334155;-webkit-text-size-adjust:100%;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc;padding:32px 12px;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;background-color:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.08);border:1px solid #e2e8f0;">

        <!-- ▸ Header -->
        {header_html}

        <!-- ▸ Main Body -->
        <tr>
          <td style="padding:32px 28px;">
            <div style="background-color:#f0f9ff;border:1px solid #bae6fd;border-radius:12px;padding:14px 18px;margin-bottom:24px;">
              <span style="font-size:12px;font-weight:700;color:#0284c7;text-transform:uppercase;letter-spacing:0.5px;">New Shipment Registered</span>
            </div>

            <h1 style="margin:0 0 10px;font-size:22px;font-weight:800;color:#0f172a;letter-spacing:-0.3px;">Shipment Confirmation</h1>
            <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;">
              Hello <strong style="color:#0f172a;">{package.recipient_name}</strong>, a new shipment has been created for you and is now active in the GoExpressly logistics network.
            </p>

            <!-- Tracking ID Chip -->
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#0f172a;border-radius:12px;margin-bottom:24px;color:#ffffff;">
              <tr>
                <td style="padding:20px;text-align:center;">
                  <span style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#94a3b8;display:block;margin-bottom:4px;">Tracking ID</span>
                  <span style="font-family:'SF Mono',Consolas,Monaco,monospace;font-size:22px;font-weight:700;color:#38bdf8;letter-spacing:1px;">{package.tracking_id}</span>
                </td>
              </tr>
            </table>

            <!-- Details Grid -->
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;margin-bottom:28px;font-size:13px;">
              <tr style="background-color:#f8fafc;">
                <td style="padding:12px 16px;font-weight:600;color:#64748b;border-bottom:1px solid #e2e8f0;width:120px;">Origin</td>
                <td style="padding:12px 16px;font-weight:700;color:#0f172a;border-bottom:1px solid #e2e8f0;">{package.origin or 'N/A'}</td>
              </tr>
              <tr>
                <td style="padding:12px 16px;font-weight:600;color:#64748b;border-bottom:1px solid #e2e8f0;width:120px;">Destination</td>
                <td style="padding:12px 16px;font-weight:700;color:#0f172a;border-bottom:1px solid #e2e8f0;">{package.destination or 'N/A'}</td>
              </tr>
              <tr style="background-color:#f8fafc;">
                <td style="padding:12px 16px;font-weight:600;color:#64748b;border-bottom:1px solid #e2e8f0;width:120px;">Carrier</td>
                <td style="padding:12px 16px;color:#334155;border-bottom:1px solid #e2e8f0;">GoExpressly Express</td>
              </tr>
              <tr>
                <td style="padding:12px 16px;font-weight:600;color:#64748b;width:120px;">Est. Delivery</td>
                <td style="padding:12px 16px;font-weight:700;color:#0284c7;">{est_date}</td>
              </tr>
            </table>

            <!-- CTA Button -->
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td align="center">
                  <a href="{track_url}" target="_blank" style="display:inline-block;background-color:#0EA5E9;color:#ffffff;font-size:15px;font-weight:700;text-decoration:none;padding:14px 36px;border-radius:10px;box-shadow:0 4px 12px rgba(14,165,233,0.35);">
                    Track Now &rarr;
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ▸ Footer -->
        <tr>
          <td style="background-color:#f8fafc;padding:24px 32px;border-top:1px solid #e2e8f0;text-align:center;">
            <p style="margin:0 0 6px;font-size:12px;color:#64748b;font-weight:600;">GoExpressly Global Logistics Inc. • Irving, Texas</p>
            <p style="margin:0;font-size:11px;color:#94a3b8;">Automated notification system. Replies to this email are not monitored.</p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _build_creation_text(package: Package) -> str:
    track_url = _get_track_url(package.tracking_id)
    return (
        f"GoExpressly Shipment Registered\n\n"
        f"Hello {package.recipient_name},\n\n"
        f"Your shipment has been registered in our network.\n"
        f"Tracking ID: {package.tracking_id}\n"
        f"Origin: {package.origin or 'N/A'}\n"
        f"Destination: {package.destination or 'N/A'}\n"
        f"Carrier: GoExpressly Express\n\n"
        f"Track your package live: {track_url}\n\n"
        f"GoExpressly Logistics • Irving, Texas"
    )


def _build_update_subject(package: Package, event: TrackingEvent) -> str:
    return f"[GoExpressly] Update for your shipment {package.tracking_id}"


def _build_update_html(package: Package, event: TrackingEvent) -> str:
    track_url = _get_track_url(package.tracking_id)
    header_html = _get_branded_header_html()

    return f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#334155;-webkit-text-size-adjust:100%;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc;padding:32px 12px;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;background-color:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.08);border:1px solid #e2e8f0;">

        <!-- ▸ Header -->
        {header_html}

        <!-- ▸ Main Body -->
        <tr>
          <td style="padding:32px 28px;">
            <div style="background-color:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:14px 18px;margin-bottom:24px;">
              <span style="font-size:12px;font-weight:700;color:#16a34a;text-transform:uppercase;letter-spacing:0.5px;">Live Status Update</span>
            </div>

            <h1 style="margin:0 0 10px;font-size:22px;font-weight:800;color:#0f172a;letter-spacing:-0.3px;">Shipment Movement</h1>
            <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;">
              Hello <strong style="color:#0f172a;">{package.recipient_name}</strong>, your package <strong style="color:#0f172a;">{package.tracking_id}</strong> has a new tracking update.
            </p>

            <!-- Status Event Card -->
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;margin-bottom:28px;font-size:13px;">
              <tr style="background-color:#f8fafc;">
                <td style="padding:14px 16px;font-weight:600;color:#64748b;border-bottom:1px solid #e2e8f0;width:120px;">New Status</td>
                <td style="padding:14px 16px;font-weight:800;color:#0284c7;font-size:15px;border-bottom:1px solid #e2e8f0;">{event.status_label}</td>
              </tr>
              <tr>
                <td style="padding:14px 16px;font-weight:600;color:#64748b;border-bottom:1px solid #e2e8f0;width:120px;">Location</td>
                <td style="padding:14px 16px;color:#0f172a;font-weight:600;border-bottom:1px solid #e2e8f0;">📍 {event.location or 'In Transit'}</td>
              </tr>
              <tr style="background-color:#f8fafc;">
                <td style="padding:14px 16px;font-weight:600;color:#64748b;width:120px;">Timestamp</td>
                <td style="padding:14px 16px;color:#334155;">{event.timestamp.strftime('%d %b %Y, %H:%M UTC')}</td>
              </tr>
            </table>

            <!-- CTA Button -->
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td align="center">
                  <a href="{track_url}" target="_blank" style="display:inline-block;background-color:#0EA5E9;color:#ffffff;font-size:15px;font-weight:700;text-decoration:none;padding:14px 36px;border-radius:10px;box-shadow:0 4px 12px rgba(14,165,233,0.35);">
                    Track Package Now &rarr;
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ▸ Footer -->
        <tr>
          <td style="background-color:#f8fafc;padding:24px 32px;border-top:1px solid #e2e8f0;text-align:center;">
            <p style="margin:0 0 6px;font-size:12px;color:#64748b;font-weight:600;">GoExpressly Global Logistics Inc. • Irving, Texas</p>
            <p style="margin:0;font-size:11px;color:#94a3b8;">Automated notification system. Replies to this email are not monitored.</p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _build_update_text(package: Package, event: TrackingEvent) -> str:
    track_url = _get_track_url(package.tracking_id)
    return (
        f"GoExpressly Shipment Update\n\n"
        f"Hello {package.recipient_name},\n\n"
        f"Tracking ID: {package.tracking_id}\n"
        f"Status: {event.status_label}\n"
        f"Location: {event.location or 'N/A'}\n"
        f"Time: {event.timestamp.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"Track package online: {track_url}\n\n"
        f"GoExpressly Logistics • Irving, Texas"
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


# ── Public entry points (called by BackgroundTask) ─────────────────────────

def send_creation_email(package_id: uuid.UUID) -> None:
    """
    Compose and send initial confirmation email to recipient upon package creation.
    """
    db = SessionLocal()
    try:
        package = db.query(Package).get(package_id)
        if not package or not package.recipient_email:
            print(f"[email_service] Package {package_id} not found or missing email")
            return

        subject = _build_creation_subject(package)
        html = _build_creation_html(package)
        text = _build_creation_text(package)
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
            print(f"[email_service] Failed to send creation email to {to_email}: {exc}")

        finally:
            try:
                log = EmailLog(
                    package_id=package.id,
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


def send_update_email(
    package_id: uuid.UUID,
    event_id: uuid.UUID,
) -> None:
    """
    Compose and send a notification email for a new tracking event.
    """
    db = SessionLocal()
    try:
        package = db.query(Package).get(package_id)
        event = db.query(TrackingEvent).get(event_id)

        if not package or not event:
            print(f"[email_service] Missing package {package_id} or event {event_id}")
            return

        subject = _build_update_subject(package, event)
        html = _build_update_html(package, event)
        text = _build_update_text(package, event)
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
            print(f"[email_service] Failed to send update email to {to_email}: {exc}")

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

