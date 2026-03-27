"""Tests for CRUD operations on /api/whitelists."""

import json

from app.database import Room, WhitelistTemplate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_whitelist(client, auth_headers, room_id, *, name="Test-Liste", urls=None):
    """Create a whitelist via the API and return the response body."""
    resp = client.post(
        "/api/whitelists",
        json={"name": name, "urls": urls or ["example.com"], "room_id": room_id},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# GET /api/whitelists
# ---------------------------------------------------------------------------


def test_get_whitelists_empty(client, auth_headers):
    resp = client.get("/api/whitelists", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_whitelists_returns_created_entry(client, auth_headers, room):
    _create_whitelist(client, auth_headers, room.id)
    resp = client.get("/api/whitelists", headers=auth_headers)
    assert len(resp.json()) == 1


def test_get_whitelists_filtered_by_room(client, auth_headers, room, db):
    other = Room(
        name="Zimmer 2", subnet="10.3.19.0/24", vlan_id=19, internet_enabled=True
    )
    db.add(other)
    db.flush()
    db.add_all(
        [
            WhitelistTemplate(
                name="Liste A", urls=json.dumps(["google.com"]), room_id=room.id
            ),
            WhitelistTemplate(
                name="Liste B", urls=json.dumps(["bing.com"]), room_id=other.id
            ),
        ]
    )
    db.commit()

    resp = client.get(f"/api/whitelists?room_id={room.id}", headers=auth_headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["name"] == "Liste A"


def test_get_whitelists_requires_auth(client):
    assert client.get("/api/whitelists").status_code == 401


# ---------------------------------------------------------------------------
# POST /api/whitelists
# ---------------------------------------------------------------------------


def test_create_whitelist_success(client, auth_headers, room):
    resp = client.post(
        "/api/whitelists",
        json={
            "name": "Google Suite",
            "urls": ["google.com", "drive.google.com"],
            "room_id": room.id,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Google Suite"
    assert "google.com" in body["urls"]
    assert "drive.google.com" in body["urls"]
    assert body["room_id"] == room.id


def test_create_whitelist_normalizes_url(client, auth_headers, room):
    resp = client.post(
        "/api/whitelists",
        json={"name": "Test", "urls": ["https://EXAMPLE.COM/pfad"], "room_id": room.id},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["urls"] == ["example.com"]


def test_create_whitelist_deduplicates_urls(client, auth_headers, room):
    resp = client.post(
        "/api/whitelists",
        json={
            "name": "Dupes",
            "urls": ["example.com", "https://example.com/x", "example.com"],
            "room_id": room.id,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["urls"] == ["example.com"]


def test_create_whitelist_rejects_invalid_url(client, auth_headers, room):
    resp = client.post(
        "/api/whitelists",
        json={"name": "Bad", "urls": ["not!valid.com"], "room_id": room.id},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_whitelist_rejects_single_label_host(client, auth_headers, room):
    resp = client.post(
        "/api/whitelists",
        json={"name": "Bad", "urls": ["asdf"], "room_id": room.id},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_whitelist_rejects_empty_urls(client, auth_headers, room):
    resp = client.post(
        "/api/whitelists",
        json={"name": "Leer", "urls": [], "room_id": room.id},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_whitelist_unknown_room_returns_404(client, auth_headers):
    resp = client.post(
        "/api/whitelists",
        json={"name": "Test", "urls": ["example.com"], "room_id": 9999},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_create_whitelist_requires_auth(client, room):
    resp = client.post(
        "/api/whitelists",
        json={"name": "Test", "urls": ["example.com"], "room_id": room.id},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PUT /api/whitelists/{id}
# ---------------------------------------------------------------------------


def test_update_whitelist_success(client, auth_headers, room):
    wl = _create_whitelist(client, auth_headers, room.id, name="Original")

    resp = client.put(
        f"/api/whitelists/{wl['id']}",
        json={"name": "Aktualisiert", "urls": ["microsoft.com"], "room_id": room.id},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Aktualisiert"
    assert body["urls"] == ["microsoft.com"]


def test_update_whitelist_persists_to_db(client, auth_headers, room, db):
    wl = _create_whitelist(client, auth_headers, room.id)

    client.put(
        f"/api/whitelists/{wl['id']}",
        json={"name": "Neu", "urls": ["updated.com"], "room_id": room.id},
        headers=auth_headers,
    )

    template = db.query(WhitelistTemplate).filter_by(id=wl["id"]).first()
    assert template.name == "Neu"
    assert template.url_list == ["updated.com"]


def test_update_whitelist_not_found_returns_404(client, auth_headers, room):
    resp = client.put(
        "/api/whitelists/9999",
        json={"name": "X", "urls": ["example.com"], "room_id": room.id},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_update_whitelist_requires_auth(client, room):
    resp = client.put(
        "/api/whitelists/1",
        json={"name": "X", "urls": ["example.com"], "room_id": room.id},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /api/whitelists/{id}
# ---------------------------------------------------------------------------


def test_delete_whitelist_success(client, auth_headers, room):
    wl = _create_whitelist(client, auth_headers, room.id)

    resp = client.delete(f"/api/whitelists/{wl['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_delete_whitelist_removes_from_db(client, auth_headers, room, db):
    wl = _create_whitelist(client, auth_headers, room.id)

    client.delete(f"/api/whitelists/{wl['id']}", headers=auth_headers)

    assert db.query(WhitelistTemplate).filter_by(id=wl["id"]).first() is None


def test_delete_whitelist_not_found_returns_404(client, auth_headers):
    resp = client.delete("/api/whitelists/9999", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_whitelist_requires_auth(client):
    resp = client.delete("/api/whitelists/1")
    assert resp.status_code == 401
