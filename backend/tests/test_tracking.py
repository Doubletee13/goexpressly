"""
tests/test_tracking.py — Tracking events and public lookup tests.

Email sending is patched out so tests run without network access.
"""
from unittest.mock import patch

PACKAGE_PAYLOAD = {
    "recipient_name": "Alice Smith",
    "recipient_email": "alice@example.com",
    "origin": "Port Harcourt, Nigeria",
    "destination": "London, UK",
}


def _create_package(client, auth_headers) -> dict:
    resp = client.post("/api/packages", json=PACKAGE_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()


def test_add_tracking_event(client, auth_headers):
    pkg = _create_package(client, auth_headers)
    pkg_id = pkg["id"]

    with patch("app.services.email_service.send_update_email"):
        resp = client.post(
            f"/api/packages/{pkg_id}/events",
            json={"status_label": "In transit", "location": "Lagos Hub"},
            headers=auth_headers,
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status_label"] == "In transit"
    assert data["location"] == "Lagos Hub"


def test_add_event_updates_package_status(client, auth_headers):
    pkg = _create_package(client, auth_headers)
    pkg_id = pkg["id"]

    with patch("app.services.email_service.send_update_email"):
        client.post(
            f"/api/packages/{pkg_id}/events",
            json={"status_label": "Arrived at Heathrow", "location": "London, UK"},
            headers=auth_headers,
        )

    get_resp = client.get(f"/api/packages/{pkg_id}", headers=auth_headers)
    updated = get_resp.json()
    assert updated["current_status"] == "Arrived at Heathrow"
    assert updated["current_location"] == "London, UK"


def test_list_events_ordered(client, auth_headers):
    pkg = _create_package(client, auth_headers)
    pkg_id = pkg["id"]

    with patch("app.services.email_service.send_update_email"):
        client.post(
            f"/api/packages/{pkg_id}/events",
            json={"status_label": "First stop", "location": "Lagos"},
            headers=auth_headers,
        )
        client.post(
            f"/api/packages/{pkg_id}/events",
            json={"status_label": "Second stop", "location": "Amsterdam"},
            headers=auth_headers,
        )

    resp = client.get(f"/api/packages/{pkg_id}/events", headers=auth_headers)
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) >= 2
    # Events should be oldest-first (ascending by timestamp)
    assert events[0]["status_label"] == "First stop"
    assert events[1]["status_label"] == "Second stop"


def test_public_tracking_lookup(client, auth_headers):
    pkg = _create_package(client, auth_headers)
    tracking_id = pkg["tracking_id"]
    pkg_id = pkg["id"]

    with patch("app.services.email_service.send_update_email"):
        client.post(
            f"/api/packages/{pkg_id}/events",
            json={"status_label": "Cleared customs", "location": "London"},
            headers=auth_headers,
        )

    # Unauthenticated public lookup
    resp = client.get(f"/api/track/{tracking_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tracking_id"] == tracking_id
    assert data["current_status"] == "Cleared customs"
    assert len(data["history"]) >= 1
    # Admin notes must NOT appear in public response
    for event in data["history"]:
        assert "notes" not in event


def test_public_tracking_invalid_id(client):
    resp = client.get("/api/track/GX-DOESNOTEXIST")
    assert resp.status_code == 404


def test_public_tracking_no_auth_required(client, auth_headers):
    pkg = _create_package(client, auth_headers)
    # No auth headers — should still succeed
    resp = client.get(f"/api/track/{pkg['tracking_id']}")
    assert resp.status_code == 200
