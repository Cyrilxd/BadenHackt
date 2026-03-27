import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, firewall
from ..audit import AuditAction, log_action
from ..database import Room, User, get_db
from ..schemas import RoomResponse, ToggleResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["rooms"])


@router.get("/rooms", response_model=list[RoomResponse])
async def get_rooms(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Room).order_by(Room.vlan_id).all()


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

    return {"success": True, "internet_enabled": enable, "room": room.name}
