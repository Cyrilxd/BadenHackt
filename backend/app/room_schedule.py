from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from . import firewall
from .database import Room

logger = logging.getLogger(__name__)

SCHEDULE_TIMEZONE = ZoneInfo("Europe/Zurich")


@dataclass(frozen=True)
class RoomScheduleState:
    internet_enabled: bool
    control_mode: str
    schedule_target_enabled: bool | None


def _now_local() -> datetime:
    return datetime.now(SCHEDULE_TIMEZONE)


def _parse_time(value: str | None) -> tuple[int, int] | None:
    if value is None:
        return None
    hour_text, minute_text = value.split(":", maxsplit=1)
    hour = int(hour_text)
    minute = int(minute_text)
    return hour, minute


def schedule_target_enabled(room: Room, now: datetime | None = None) -> bool | None:
    if not room.schedule_enabled:
        return None

    open_time = _parse_time(room.schedule_open_time)
    lock_time = _parse_time(room.schedule_lock_time)
    if open_time is None or lock_time is None:
        return None

    current = now or _now_local()
    minutes_now = current.hour * 60 + current.minute
    open_minutes = open_time[0] * 60 + open_time[1]
    lock_minutes = lock_time[0] * 60 + lock_time[1]

    # Innerhalb des Zeitfensters (open_time bis lock_time) ist Internet GESPERRT.
    # Ausserhalb des Zeitfensters ist Internet freigegeben.
    if open_minutes < lock_minutes:
        in_window = open_minutes <= minutes_now < lock_minutes
    else:
        in_window = minutes_now >= open_minutes or minutes_now < lock_minutes

    return not in_window  # gesperrt im Fenster = internet_enabled False


def resolve_room_state(room: Room, now: datetime | None = None) -> RoomScheduleState:
    schedule_enabled_now = schedule_target_enabled(room, now)

    if room.manual_override_active and room.manual_override_enabled is not None:
        return RoomScheduleState(
            internet_enabled=room.manual_override_enabled,
            control_mode="manual_override",
            schedule_target_enabled=schedule_enabled_now,
        )

    if schedule_enabled_now is not None:
        return RoomScheduleState(
            internet_enabled=schedule_enabled_now,
            control_mode="schedule",
            schedule_target_enabled=schedule_enabled_now,
        )

    return RoomScheduleState(
        internet_enabled=room.internet_enabled,
        control_mode="manual",
        schedule_target_enabled=None,
    )


def apply_room_state(room: Room, now: datetime | None = None) -> bool:
    resolved = resolve_room_state(room, now)
    changed = room.internet_enabled != resolved.internet_enabled
    room.internet_enabled = resolved.internet_enabled
    return changed


def sync_scheduled_rooms(db: Session, now: datetime | None = None) -> list[int]:
    rooms = db.query(Room).order_by(Room.vlan_id).all()
    changed_room_ids: list[int] = []

    for room in rooms:
        if apply_room_state(room, now):
            changed_room_ids.append(room.id)

    if not changed_room_ids:
        return []

    db.flush()
    firewall.FirewallManager.sync_room_policies(db, changed_room_ids)
    db.commit()
    logger.info("Applied timed room schedule to rooms: %s", changed_room_ids)
    return changed_room_ids
