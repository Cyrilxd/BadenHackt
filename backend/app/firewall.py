import json
import logging
import os
from typing import Iterable
from urllib import error, request

from sqlalchemy.orm import Session

from .database import Room, WhitelistTemplate

logger = logging.getLogger(__name__)

FIREWALL_API_URL = os.environ.get("FIREWALL_API_URL", "").rstrip("/")
FIREWALL_API_TOKEN = os.environ.get("FIREWALL_API_TOKEN", "")
FIREWALL_API_TIMEOUT = float(os.environ.get("FIREWALL_API_TIMEOUT", "5"))


class FirewallSyncError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if FIREWALL_API_TOKEN:
        headers["X-Firewall-Token"] = FIREWALL_API_TOKEN
    return headers


def _request_json(method: str, path: str, payload: dict | None = None) -> dict:
    if not FIREWALL_API_URL:
        raise FirewallSyncError("FIREWALL_API_URL is not configured")

    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    http_request = request.Request(
        url=f"{FIREWALL_API_URL}{path}",
        data=body,
        headers=_headers(),
        method=method,
    )

    try:
        with request.urlopen(http_request, timeout=FIREWALL_API_TIMEOUT) as response:
            raw_body = response.read().decode("utf-8").strip()
    except error.HTTPError as exc:
        error_body = exc.read().decode("utf-8").strip()
        detail = error_body or exc.reason
        raise FirewallSyncError(
            f"firewall API returned HTTP {exc.code}: {detail}"
        ) from exc
    except error.URLError as exc:
        raise FirewallSyncError(f"firewall API is unreachable: {exc.reason}") from exc
    except TimeoutError as exc:
        raise FirewallSyncError("firewall API request timed out") from exc

    if not raw_body:
        return {}

    try:
        return json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise FirewallSyncError("firewall API returned invalid JSON") from exc


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _room_whitelist_entries(db: Session, room_id: int) -> list[str]:
    entries: list[str] = []
    templates = (
        db.query(WhitelistTemplate)
        .filter(
            WhitelistTemplate.room_id == room_id,
            WhitelistTemplate.is_active == True,
        )
        .order_by(WhitelistTemplate.id.asc())
        .all()
    )
    for template in templates:
        entries.extend(template.url_list)
    return _dedupe(entries)


def _room_policy_payload(db: Session, room_id: int) -> dict:
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise FirewallSyncError(
            f"room {room_id} not found while building firewall policy"
        )

    return {
        "vlan_id": room.vlan_id,
        "room_name": room.name,
        "subnet": room.subnet,
        "internet_enabled": room.internet_enabled,
        "whitelist_entries": _room_whitelist_entries(db, room.id),
    }


class FirewallManager:
    @staticmethod
    def sync_room_policies(db: Session, room_ids: Iterable[int]) -> None:
        unique_room_ids = []
        seen_room_ids: set[int] = set()
        for room_id in room_ids:
            if room_id in seen_room_ids:
                continue
            seen_room_ids.add(room_id)
            unique_room_ids.append(room_id)

        if not unique_room_ids:
            return

        payload = {
            "rooms": [_room_policy_payload(db, room_id) for room_id in unique_room_ids]
        }
        response = _request_json("PUT", "/rooms/policies", payload)
        synced_rooms = len(response.get("rooms", []))
        logger.info(
            "Synchronized %d room policy entries with firewall agent", synced_rooms
        )

    @staticmethod
    def sync_all_rooms(db: Session) -> None:
        room_ids = [
            room_id for (room_id,) in db.query(Room.id).order_by(Room.vlan_id).all()
        ]
        FirewallManager.sync_room_policies(db, room_ids)