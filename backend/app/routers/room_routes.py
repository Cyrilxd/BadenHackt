import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, firewall
from ..database import Room, User, get_db
from ..schemas import RoomResponse, ToggleResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["rooms"])


@router.get("/rooms", response_model=list[RoomResponse])
async def get_rooms(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    rooms = db.query(Room).order_by(Room.vlan_id).all()

    for room in rooms:
        room.internet_enabled = firewall.FirewallManager.get_vlan_status(room.subnet)

    return rooms


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

    if enable:
        success = firewall.FirewallManager.unblock_vlan(room.vlan_id, room.subnet)
    else:
        success = firewall.FirewallManager.block_vlan(room.vlan_id, room.subnet)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update firewall rules")

    room.internet_enabled = enable
    db.commit()

    logger.info(
        "User %s %s internet for %s (VLAN %d)",
        current_user.username,
        "enabled" if enable else "disabled",
        room.name,
        room.vlan_id,
    )

    return {"success": True, "internet_enabled": enable, "room": room.name}
