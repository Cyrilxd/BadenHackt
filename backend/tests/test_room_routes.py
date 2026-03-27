"""Tests for room listing, manual toggle overrides, and timed schedules."""

from datetime import datetime
from unittest.mock import patch

from app.database import Room

# ---------------------------------------------------------------------------
# GET /api/rooms
# ---------------------------------------------------------------------------


def test_get_rooms_empty_list(client, auth_headers):
    resp = client.get("/api/rooms", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_rooms_returns_seeded_room(client, auth_headers, room):
    resp = client.get("/api/rooms", headers=auth_headers)
    assert resp.status_code == 200
    rooms = resp.json()
    assert len(rooms) == 1
    assert rooms[0]["name"] == room.name
    assert rooms[0]["vlan_id"] == room.vlan_id
    assert rooms[0]["internet_enabled"] is True


def test_get_rooms_returns_all_fields(client, auth_headers, room):
    data = client.get("/api/rooms", headers=auth_headers).json()[0]
    assert set(data.keys()) >= {
        "id",
        "name",
        "subnet",
        "vlan_id",
        "internet_enabled",
        "schedule_enabled",
        "schedule_open_time",
        "schedule_lock_time",
        "manual_override_active",
        "manual_override_enabled",
        "control_mode",
        "schedule_target_enabled",
    }


def test_get_rooms_ordered_by_vlan_id(client, auth_headers, db):
    db.add_all(
        [
            Room(
                name="Zimmer 3",
                subnet="10.3.20.0/24",
                vlan_id=20,
                internet_enabled=True,
            ),
            Room(
                name="Zimmer 1",
                subnet="10.3.18.0/24",
                vlan_id=18,
                internet_enabled=True,
            ),
            Room(
                name="Zimmer 2",
                subnet="10.3.19.0/24",
                vlan_id=19,
                internet_enabled=True,
            ),
        ]
    )
    db.commit()

    resp = client.get("/api/rooms", headers=auth_headers)
    vlans = [r["vlan_id"] for r in resp.json()]
    assert vlans == sorted(vlans)


def test_get_rooms_requires_auth(client, room):
    resp = client.get("/api/rooms")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/rooms/{id}/toggle
# ---------------------------------------------------------------------------


def test_toggle_disables_internet(client, auth_headers, room):
    resp = client.post(
        f"/api/rooms/{room.id}/toggle",
        params={"enable": "false"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["internet_enabled"] is False
    assert body["room"] == room.name
    assert body["manual_override_active"] is True
    assert body["control_mode"] == "manual_override"


def test_toggle_enables_internet(client, auth_headers, room, db):
    room.internet_enabled = False
    db.commit()

    resp = client.post(
        f"/api/rooms/{room.id}/toggle",
        params={"enable": "true"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["internet_enabled"] is True


def test_toggle_persists_change_to_db(client, auth_headers, room, db):
    client.post(
        f"/api/rooms/{room.id}/toggle",
        params={"enable": "false"},
        headers=auth_headers,
    )
    db.refresh(room)
    assert room.internet_enabled is False
    assert room.manual_override_active is True
    assert room.manual_override_enabled is False


def test_toggle_unknown_room_returns_404(client, auth_headers):
    resp = client.post(
        "/api/rooms/9999/toggle",
        params={"enable": "false"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_toggle_requires_auth(client, room):
    resp = client.post(
        f"/api/rooms/{room.id}/toggle",
        params={"enable": "false"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PUT /api/rooms/{id}/schedule
# ---------------------------------------------------------------------------


def test_update_schedule_persists_times(client, auth_headers, room, db):
    resp = client.put(
        f"/api/rooms/{room.id}/schedule",
        json={
            "schedule_enabled": True,
            "schedule_open_time": "08:00",
            "schedule_lock_time": "15:30",
            "clear_override": False,
        },
        headers=auth_headers,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["schedule_enabled"] is True
    assert body["schedule_open_time"] == "08:00"
    assert body["schedule_lock_time"] == "15:30"
    db.refresh(room)
    assert room.schedule_enabled is True
    assert room.schedule_open_time == "08:00"
    assert room.schedule_lock_time == "15:30"


def test_update_schedule_clears_manual_override_when_requested(
    client, auth_headers, room, db
):
    room.manual_override_active = True
    room.manual_override_enabled = False
    room.schedule_enabled = True
    room.schedule_open_time = "08:00"
    room.schedule_lock_time = "16:00"
    room.internet_enabled = False
    db.commit()

    with patch(
        "app.room_schedule._now_local",
        return_value=datetime(2026, 3, 27, 10, 0),
    ):
        resp = client.put(
            f"/api/rooms/{room.id}/schedule",
            json={
                "schedule_enabled": True,
                "schedule_open_time": "08:00",
                "schedule_lock_time": "16:00",
                "clear_override": True,
            },
            headers=auth_headers,
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["manual_override_active"] is False
    assert body["internet_enabled"] is True
    assert body["control_mode"] == "schedule"
    db.refresh(room)
    assert room.manual_override_active is False
    assert room.manual_override_enabled is None
    assert room.internet_enabled is True


def test_get_rooms_applies_schedule_when_no_override(client, auth_headers, room, db):
    room.schedule_enabled = True
    room.schedule_open_time = "08:00"
    room.schedule_lock_time = "16:00"
    room.internet_enabled = False
    db.commit()

    with patch(
        "app.room_schedule._now_local",
        return_value=datetime(2026, 3, 27, 9, 0),
    ):
        resp = client.get("/api/rooms", headers=auth_headers)

    assert resp.status_code == 200
    body = resp.json()[0]
    assert body["internet_enabled"] is True
    assert body["control_mode"] == "schedule"
    assert body["schedule_target_enabled"] is True
    db.refresh(room)
    assert room.internet_enabled is True


def test_get_rooms_keeps_manual_override_over_schedule(client, auth_headers, room, db):
    room.schedule_enabled = True
    room.schedule_open_time = "08:00"
    room.schedule_lock_time = "16:00"
    room.manual_override_active = True
    room.manual_override_enabled = False
    room.internet_enabled = False
    db.commit()

    with patch(
        "app.room_schedule._now_local",
        return_value=datetime(2026, 3, 27, 9, 0),
    ):
        resp = client.get("/api/rooms", headers=auth_headers)

    assert resp.status_code == 200
    body = resp.json()[0]
    assert body["internet_enabled"] is False
    assert body["control_mode"] == "manual_override"
    assert body["schedule_target_enabled"] is True


def test_update_schedule_rejects_equal_times(client, auth_headers, room):
    resp = client.put(
        f"/api/rooms/{room.id}/schedule",
        json={
            "schedule_enabled": True,
            "schedule_open_time": "08:00",
            "schedule_lock_time": "08:00",
        },
        headers=auth_headers,
    )

    assert resp.status_code == 422
