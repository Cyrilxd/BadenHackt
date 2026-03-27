import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, firewall
from ..audit import AuditAction, log_action
from ..database import Room, User, get_db
from ..room_schedule import apply_room_state, resolve_room_state
from ..schemas import RoomResponse, RoomScheduleUpdate, ToggleResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["rooms"])


def _room_response(room: Room) -> RoomResponse:
    resolved = resolve_room_state(room)
    return RoomResponse(
        id=room.id,
        name=room.name,
        subnet=room.subnet,
        vlan_id=room.vlan_id,
        internet_enabled=room.internet_enabled,
        schedule_enabled=room.schedule_enabled,
        schedule_open_time=room.schedule_open_time,
        schedule_lock_time=room.schedule_lock_time,
        manual_override_active=room.manual_override_active,
        manual_override_enabled=room.manual_override_enabled,
        control_mode=resolved.control_mode,
        schedule_target_enabled=resolved.schedule_target_enabled,
    )


@router.get("/rooms", response_model=list[RoomResponse])
async def get_rooms(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    rooms = db.query(Room).order_by(Room.vlan_id).all()
    changed_room_ids: list[int] = []

    for room in rooms:
        if apply_room_state(room):
            changed_room_ids.append(room.id)

    if changed_room_ids:
        try:
            db.flush()
            firewall.FirewallManager.sync_room_policies(db, changed_room_ids)
        except firewall.FirewallSyncError as exc:
            db.rollback()
            raise HTTPException(
                status_code=502,
                detail=f"Failed to update firewall rules: {exc}",
            ) from exc
        db.commit()
        rooms = db.query(Room).order_by(Room.vlan_id).all()

    return [_room_response(room) for room in rooms]


@router.post("/rooms/{room_id}/toggle", response_model=ToggleResponse)
async def toggle_internet(
    room_id: int,
    enable: bool,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    room.manual_override_active = True
    room.manual_override_enabled = enable
    room.internet_enabled = enable
    db.flush()

    try:
        firewall.FirewallManager.sync_room_policies(db, [room.id])
    except firewall.FirewallSyncError as exc:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Failed to update firewall rules: {exc}",
        ) from exc

    db.commit()

    logger.info(
        "User %s %s internet for %s (VLAN %d)",
        current_user.username,
        "enabled" if enable else "disabled",
        room.name,
        room.vlan_id,
    )

    log_action(
        db,
        username=current_user.username,
        action=AuditAction.INTERNET_TOGGLE,
        target=f"{room.name} (VLAN {room.vlan_id})",
        detail={"enabled": enable},
    )

    return {
        "success": True,
        "internet_enabled": enable,
        "room": room.name,
        "manual_override_active": room.manual_override_active,
        "control_mode": "manual_override",
    }


@router.put("/rooms/{room_id}/schedule", response_model=RoomResponse)
async def update_room_schedule(
    room_id: int,
    payload: RoomScheduleUpdate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    room.schedule_enabled = payload.schedule_enabled
    room.schedule_open_time = (
        payload.schedule_open_time if payload.schedule_enabled else None
    )
    room.schedule_lock_time = (
        payload.schedule_lock_time if payload.schedule_enabled else None
    )

    if payload.schedule_enabled and (
        not room.schedule_open_time or not room.schedule_lock_time
    ):
        raise HTTPException(
            status_code=422,
            detail="Open and lock time are required when the schedule is enabled",
        )

    if payload.clear_override:
        room.manual_override_active = False
        room.manual_override_enabled = None

    apply_room_state(room)
    db.flush()

    try:
        firewall.FirewallManager.sync_room_policies(db, [room.id])
    except firewall.FirewallSyncError as exc:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Failed to update firewall rules: {exc}",
        ) from exc

    db.commit()
    db.refresh(room)

    logger.info(
        "User %s updated schedule for %s (VLAN %d)",
        current_user.username,
        room.name,
        room.vlan_id,
    )

    log_action(
        db,
        username=current_user.username,
        action=AuditAction.INTERNET_TOGGLE,
        target=f"{room.name} (VLAN {room.vlan_id})",
        detail={
            "schedule_enabled": room.schedule_enabled,
            "schedule_open_time": room.schedule_open_time,
            "schedule_lock_time": room.schedule_lock_time,
            "clear_override": payload.clear_override,
        },
    )

    return _room_response(room)
