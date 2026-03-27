from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import json
import logging

from . import database, auth, firewall
from .database import get_db, init_db, User, Room, WhitelistTemplate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Internet EIN/AUS API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()
    logger.info("Database initialized")

# Pydantic models for request/response
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class RoomResponse(BaseModel):
    id: int
    name: str
    subnet: str
    vlan_id: int
    internet_enabled: bool
    
    class Config:
        from_attributes = True

class WhitelistCreate(BaseModel):
    name: str
    urls: List[str]
    room_id: int

class WhitelistResponse(BaseModel):
    id: int
    name: str
    urls: List[str]
    room_id: int
    
    class Config:
        from_attributes = True

# Routes
@app.post("/api/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login endpoint - returns JWT token. ANY valid user can access ALL rooms."""
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
        "user": {
            "username": user.username,
            "role": "teacher"  # All users are teachers with full access
        }
    }

@app.get("/api/rooms", response_model=List[RoomResponse])
async def get_rooms(current_user: User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Get ALL rooms - every teacher can see and control all rooms"""
    rooms = db.query(Room).order_by(Room.vlan_id).all()
    
    # Update internet_enabled status from actual firewall state
    for room in rooms:
        room.internet_enabled = firewall.FirewallManager.get_vlan_status(room.subnet)
    
    db.commit()
    
    return rooms

@app.post("/api/rooms/{room_id}/toggle")
async def toggle_internet(
    room_id: int,
    enable: bool,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle internet access for ANY room - no authorization check (all teachers can control all rooms)"""
    room = db.query(Room).filter(Room.id == room_id).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Apply firewall rule
    fw_manager = firewall.FirewallManager()
    
    if enable:
        success = fw_manager.unblock_vlan(room.vlan_id, room.subnet)
    else:
        success = fw_manager.block_vlan(room.vlan_id, room.subnet)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update firewall rules")
    
    # Update database
    room.internet_enabled = enable
    db.commit()
    
    logger.info(f"User {current_user.username} {'enabled' if enable else 'disabled'} internet for {room.name} (VLAN {room.vlan_id})")
    
    return {"success": True, "internet_enabled": enable, "room": room.name}

@app.get("/api/whitelists")
async def get_whitelists(
    room_id: int = None,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get whitelist templates. If room_id provided, filter by room. Otherwise return all."""
    query = db.query(WhitelistTemplate)
    
    if room_id:
        query = query.filter(WhitelistTemplate.room_id == room_id)
    
    templates = query.all()
    
    # Parse JSON urls
    result = []
    for template in templates:
        result.append({
            "id": template.id,
            "name": template.name,
            "urls": json.loads(template.urls) if template.urls else [],
            "room_id": template.room_id
        })
    
    return result

@app.post("/api/whitelists", response_model=WhitelistResponse)
async def create_whitelist(
    whitelist: WhitelistCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new whitelist template for a specific room"""
    room = db.query(Room).filter(Room.id == whitelist.room_id).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    new_template = WhitelistTemplate(
        name=whitelist.name,
        urls=json.dumps(whitelist.urls),
        room_id=whitelist.room_id
    )
    
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    
    logger.info(f"User {current_user.username} created whitelist '{whitelist.name}' for {room.name}")
    
    return {
        "id": new_template.id,
        "name": new_template.name,
        "urls": json.loads(new_template.urls),
        "room_id": new_template.room_id
    }

@app.delete("/api/whitelists/{whitelist_id}")
async def delete_whitelist(
    whitelist_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a whitelist template"""
    template = db.query(WhitelistTemplate).filter(WhitelistTemplate.id == whitelist_id).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Whitelist not found")
    
    room = db.query(Room).filter(Room.id == template.room_id).first()
    
    db.delete(template)
    db.commit()
    
    logger.info(f"User {current_user.username} deleted whitelist '{template.name}' from {room.name if room else 'unknown room'}")
    
    return {"success": True}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "internet-control-api", "version": "2.0.0"}
