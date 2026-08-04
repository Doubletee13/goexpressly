"""
tests/test_packages.py — Package CRUD endpoint tests.
"""
import re


PACKAGE_PAYLOAD = {
    "recipient_name": "Jane Doe",
    "recipient_email": "jane@example.com",
    "recipient_phone": "+2348012345678",
    "origin": "Lagos, Nigeria",
    "destination": "Abuja, Nigeria",
    "description": "Electronics",
}


def test_create_package(client, auth_headers):
    resp = client.post("/api/packages", json=PACKAGE_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert "tracking_id" in data
    # Validate format: GX- followed by 10 uppercase alphanums
    assert re.match(r"^GX-[A-Z0-9]{10}$", data["tracking_id"])
    assert data["recipient_name"] == "Jane Doe"
    assert data["current_status"] == "Package registered"


def test_create_package_unauthenticated(client):
    resp = client.post("/api/packages", json=PACKAGE_PAYLOAD)
    assert resp.status_code == 401


def test_list_packages(client, auth_headers):
    # Create two packages
    client.post("/api/packages", json=PACKAGE_PAYLOAD, headers=auth_headers)
    client.post("/api/packages", json={**PACKAGE_PAYLOAD, "recipient_email": "bob@example.com"}, headers=auth_headers)

    resp = client.get("/api/packages", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "items" in data
    assert data["total"] >= 2


def test_get_package_by_id(client, auth_headers):
    create_resp = client.post("/api/packages", json=PACKAGE_PAYLOAD, headers=auth_headers)
    pkg_id = create_resp.json()["id"]

    resp = client.get(f"/api/packages/{pkg_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == pkg_id


def test_get_package_not_found(client, auth_headers):
    resp = client.get("/api/packages/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404


def test_update_package(client, auth_headers):
    create_resp = client.post("/api/packages", json=PACKAGE_PAYLOAD, headers=auth_headers)
    pkg_id = create_resp.json()["id"]

    resp = client.patch(
        f"/api/packages/{pkg_id}",
        json={"description": "Updated description"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "Updated description"


def test_soft_delete_package(client, auth_headers):
    create_resp = client.post("/api/packages", json=PACKAGE_PAYLOAD, headers=auth_headers)
    pkg_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/packages/{pkg_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    # Should be 404 after soft-delete
    get_resp = client.get(f"/api/packages/{pkg_id}", headers=auth_headers)
    assert get_resp.status_code == 404
