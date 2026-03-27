from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json
import logging

from . import auth, firewall
from .database import get_db, init_db, User, Room, WhitelistTemplate
from .schemas import (
    Token, RoomResponse, ToggleResponse,
    WhitelistCreate, WhitelistResponse, DeleteResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized")
    yield


app = FastAPI(title="Internet EIN/AUS API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"username": user.username, "role": "teacher"},
    }


@app.get("/api/rooms", response_model=list[RoomResponse])
async def get_rooms(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    rooms = db.query(Room).order_by(Room.vlan_id).all()

    for room in rooms:
        room.internet_enabled = firewall.FirewallManager.get_vlan_status(room.subnet)

    return rooms


@app.post("/api/rooms/{room_id}/toggle", response_model=ToggleResponse)
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


@app.get("/api/whitelists", response_model=list[WhitelistResponse])
async def get_whitelists(
    room_id: int = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(WhitelistTemplate)
    if room_id:
        query = query.filter(WhitelistTemplate.room_id == room_id)

    templates = query.all()

    return [
        {
            "id": t.id,
            "name": t.name,
            "urls": json.loads(t.urls) if t.urls else [],
            "room_id": t.room_id,
        }
        for t in templates
    ]


@app.post("/api/whitelists", response_model=WhitelistResponse)
async def create_whitelist(
    whitelist: WhitelistCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == whitelist.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    new_template = WhitelistTemplate(
        name=whitelist.name,
        urls=json.dumps(whitelist.urls),
        room_id=whitelist.room_id,
    )

    db.add(new_template)
    db.commit()
    db.refresh(new_template)

    logger.info(
        "User %s created whitelist '%s' for %s",
        current_user.username, whitelist.name, room.name,
    )

    return {
        "id": new_template.id,
        "name": new_template.name,
        "urls": json.loads(new_template.urls),
        "room_id": new_template.room_id,
    }


@app.delete("/api/whitelists/{whitelist_id}", response_model=DeleteResponse)
async def delete_whitelist(
    whitelist_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    template = db.query(WhitelistTemplate).filter(WhitelistTemplate.id == whitelist_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Whitelist not found")

    template_name = template.name
    db.delete(template)
    db.commit()

    logger.info("User %s deleted whitelist '%s'", current_user.username, template_name)

    return {"success": True}


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "internet-control-api", "version": "2.0.0"}
