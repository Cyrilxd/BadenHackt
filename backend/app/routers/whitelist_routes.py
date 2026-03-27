import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, firewall
from ..audit import AuditAction, log_action
from ..database import (
    Room,
    RoomWhitelistAssignment,
    User,
    WhitelistTemplate,
    get_db,
)
from ..schemas import (
    DeleteResponse,
    WhitelistCreate,
    WhitelistResponse,
    WhitelistToggle,
    WhitelistUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["whitelists"])


def _serialize_whitelist(
    template: WhitelistTemplate,
    room_id: int,
    is_active: bool,
) -> dict:
    return {
        "id": template.id,
        "name": template.name,
        "urls": template.url_list,
        "room_id": room_id,
        "is_active": is_active,
    }


def _get_or_create_assignment(
    db: Session,
    room_id: int,
    whitelist_id: int,
) -> RoomWhitelistAssignment:
    assignment = (
        db.query(RoomWhitelistAssignment)
        .filter(
            RoomWhitelistAssignment.room_id == room_id,
            RoomWhitelistAssignment.whitelist_id == whitelist_id,
        )
        .first()
    )
    if assignment is not None:
        return assignment

    assignment = RoomWhitelistAssignment(
        room_id=room_id,
        whitelist_id=whitelist_id,
        is_active=False,
    )
    db.add(assignment)
    db.flush()
    return assignment


@router.get("/whitelists", response_model=list[WhitelistResponse])
async def get_whitelists(
    room_id: int = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    templates = db.query(WhitelistTemplate).order_by(WhitelistTemplate.id.asc()).all()

    if room_id is not None:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        assignments = {
            assignment.whitelist_id: assignment
            for assignment in db.query(RoomWhitelistAssignment)
            .filter(RoomWhitelistAssignment.room_id == room_id)
            .all()
        }
        return [
            _serialize_whitelist(
                template,
                room_id,
                assignments.get(template.id).is_active
                if assignments.get(template.id) is not None
                else False,
            )
            for template in templates
        ]

    rooms = db.query(Room).order_by(Room.vlan_id.asc()).all()
    assignments = {
        (assignment.room_id, assignment.whitelist_id): assignment.is_active
        for assignment in db.query(RoomWhitelistAssignment).all()
    }
    return [
        _serialize_whitelist(
            template,
            room.id,
            assignments.get((room.id, template.id), False),
        )
        for room in rooms
        for template in templates
    ]


@router.post("/whitelists", response_model=WhitelistResponse)
async def create_whitelist(
    whitelist: WhitelistCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == whitelist.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    template = WhitelistTemplate(name=whitelist.name)
    template.url_list = whitelist.urls

    db.add(template)
    db.flush()

    room_ids = [
        room_id for (room_id,) in db.query(Room.id).order_by(Room.vlan_id).all()
    ]
    for current_room_id in room_ids:
        db.add(
            RoomWhitelistAssignment(
                room_id=current_room_id,
                whitelist_id=template.id,
                is_active=(
                    whitelist.is_active
                    if current_room_id == whitelist.room_id
                    else False
                ),
            )
        )
    db.flush()

    try:
        firewall.FirewallManager.sync_room_policies(db, room_ids)
    except firewall.FirewallSyncError as exc:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Failed to sync whitelist with firewall: {exc}",
        ) from exc

    db.commit()
    db.refresh(template)

    logger.info(
        "User %s created whitelist '%s' for %s (active=%s)",
        current_user.username,
        whitelist.name,
        room.name,
        whitelist.is_active,
    )

    log_action(
        db,
        username=current_user.username,
        action=AuditAction.WHITELIST_CREATE,
        target=f"{whitelist.name} → {room.name}",
        detail={"urls": whitelist.urls, "active": whitelist.is_active},
    )

    return _serialize_whitelist(template, whitelist.room_id, whitelist.is_active)


@router.put("/whitelists/{whitelist_id}", response_model=WhitelistResponse)
async def update_whitelist(
    whitelist_id: int,
    whitelist: WhitelistUpdate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    template = (
        db.query(WhitelistTemplate).filter(WhitelistTemplate.id == whitelist_id).first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Whitelist not found")

    room = db.query(Room).filter(Room.id == whitelist.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    template.name = whitelist.name
    template.url_list = whitelist.urls
    assignment = _get_or_create_assignment(db, whitelist.room_id, template.id)
    assignment.is_active = whitelist.is_active

    db.flush()

    try:
        firewall.FirewallManager.sync_all_rooms(db)
    except firewall.FirewallSyncError as exc:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Failed to sync whitelist with firewall: {exc}",
        ) from exc

    db.commit()
    db.refresh(template)

    logger.info(
        "User %s updated whitelist '%s' for %s (active=%s)",
        current_user.username,
        template.name,
        room.name,
        assignment.is_active,
    )

    log_action(
        db,
        username=current_user.username,
        action=AuditAction.WHITELIST_UPDATE,
        target=f"{template.name} → {room.name}",
        detail={"urls": whitelist.urls, "active": assignment.is_active},
    )

    return _serialize_whitelist(template, whitelist.room_id, assignment.is_active)


@router.patch("/whitelists/{whitelist_id}/toggle", response_model=WhitelistResponse)
async def toggle_whitelist(
    whitelist_id: int,
    payload: WhitelistToggle,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    template = (
        db.query(WhitelistTemplate).filter(WhitelistTemplate.id == whitelist_id).first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Whitelist not found")

    room = db.query(Room).filter(Room.id == payload.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    assignment = _get_or_create_assignment(db, payload.room_id, template.id)
    assignment.is_active = payload.is_active

    db.flush()

    try:
        firewall.FirewallManager.sync_room_policies(db, [payload.room_id])
    except firewall.FirewallSyncError as exc:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Failed to sync whitelist with firewall: {exc}",
        ) from exc

    db.commit()
    db.refresh(template)

    logger.info(
        "User %s set whitelist '%s' active=%s",
        current_user.username,
        template.name,
        assignment.is_active,
    )

    log_action(
        db,
        username=current_user.username,
        action=AuditAction.WHITELIST_TOGGLE,
        target=f"{template.name} → {room.name}",
        detail={"active": assignment.is_active},
    )

    return _serialize_whitelist(template, payload.room_id, assignment.is_active)


@router.delete("/whitelists/{whitelist_id}", response_model=DeleteResponse)
async def delete_whitelist(
    whitelist_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    template = (
        db.query(WhitelistTemplate).filter(WhitelistTemplate.id == whitelist_id).first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Whitelist not found")

    template_name = template.name
    room_ids = [
        room_id
        for (room_id,) in db.query(RoomWhitelistAssignment.room_id)
        .filter(RoomWhitelistAssignment.whitelist_id == whitelist_id)
        .all()
    ]

    db.delete(template)
    db.flush()

    try:
        firewall.FirewallManager.sync_room_policies(db, room_ids)
    except firewall.FirewallSyncError as exc:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Failed to sync whitelist with firewall: {exc}",
        ) from exc

    db.commit()

    logger.info("User %s deleted whitelist '%s'", current_user.username, template_name)

    log_action(
        db,
        username=current_user.username,
        action=AuditAction.WHITELIST_DELETE,
        target=template_name,
    )

    return {"success": True}
