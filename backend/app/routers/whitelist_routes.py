import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, firewall
from ..audit import AuditAction, log_action
from ..database import Room, User, WhitelistTemplate, get_db
from ..schemas import (
    DeleteResponse,
    WhitelistCreate,
    WhitelistResponse,
    WhitelistToggle,
    WhitelistUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["whitelists"])


@router.get("/whitelists", response_model=list[WhitelistResponse])
async def get_whitelists(
    room_id: int = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(WhitelistTemplate)
    if room_id:
        query = query.filter(WhitelistTemplate.room_id == room_id)

    return [
        {
            "id": t.id,
            "name": t.name,
            "urls": t.url_list,
            "room_id": t.room_id,
            "is_active": t.is_active,
        }
        for t in query.all()
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

    template = WhitelistTemplate(
        name=whitelist.name,
        room_id=whitelist.room_id,
        is_active=whitelist.is_active,
    )
    template.url_list = whitelist.urls

    db.add(template)
    db.flush()

    try:
        firewall.FirewallManager.sync_room_policies(db, [whitelist.room_id])
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
        template.is_active,
    )

    log_action(
        db,
        username=current_user.username,
        action=AuditAction.WHITELIST_CREATE,
        target=f"{whitelist.name} → {room.name}",
        detail={"urls": whitelist.urls, "active": template.is_active},
    )

    return {
        "id": template.id,
        "name": template.name,
        "urls": template.url_list,
        "room_id": template.room_id,
        "is_active": template.is_active,
    }


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

    previous_room_id = template.room_id

    template.name = whitelist.name
    template.url_list = whitelist.urls
    template.room_id = whitelist.room_id
    template.is_active = whitelist.is_active

    db.flush()

    try:
        firewall.FirewallManager.sync_room_policies(
            db,
            list({previous_room_id, whitelist.room_id}),
        )
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
        template.is_active,
    )

    log_action(
        db,
        username=current_user.username,
        action=AuditAction.WHITELIST_UPDATE,
        target=f"{template.name} → {room.name}",
        detail={"urls": whitelist.urls, "active": template.is_active},
    )

    return {
        "id": template.id,
        "name": template.name,
        "urls": template.url_list,
        "room_id": template.room_id,
        "is_active": template.is_active,
    }


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

    template.is_active = payload.is_active
    room_id = template.room_id

    db.flush()

    try:
        firewall.FirewallManager.sync_room_policies(db, [room_id])
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
        template.is_active,
    )

    log_action(
        db,
        username=current_user.username,
        action=AuditAction.WHITELIST_TOGGLE,
        target=template.name,
        detail={"active": template.is_active},
    )

    return {
        "id": template.id,
        "name": template.name,
        "urls": template.url_list,
        "room_id": template.room_id,
        "is_active": template.is_active,
    }


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
    room_id = template.room_id

    db.delete(template)
    db.flush()

    try:
        firewall.FirewallManager.sync_room_policies(db, [room_id])
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