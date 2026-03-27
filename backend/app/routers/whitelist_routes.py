import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth
from ..database import Room, User, WhitelistTemplate, get_db
from ..schemas import (
    DeleteResponse,
    WhitelistCreate,
    WhitelistResponse,
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
    )
    template.url_list = whitelist.urls

    db.add(template)
    db.commit()
    db.refresh(template)

    logger.info(
        "User %s created whitelist '%s' for %s",
        current_user.username,
        whitelist.name,
        room.name,
    )

    return {
        "id": template.id,
        "name": template.name,
        "urls": template.url_list,
        "room_id": template.room_id,
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

    template.name = whitelist.name
    template.url_list = whitelist.urls
    template.room_id = whitelist.room_id

    db.commit()
    db.refresh(template)

    logger.info(
        "User %s updated whitelist '%s' for %s",
        current_user.username,
        template.name,
        room.name,
    )

    return {
        "id": template.id,
        "name": template.name,
        "urls": template.url_list,
        "room_id": template.room_id,
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
    db.delete(template)
    db.commit()

    logger.info("User %s deleted whitelist '%s'", current_user.username, template_name)

    return {"success": True}
