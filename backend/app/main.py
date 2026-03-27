import json
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from sqlalchemy.orm import Session

from . import auth
from .database import Room, User, WhitelistTemplate, get_db
from .init_data import init_test_data
from .routers import auth_routes, room_routes, whitelist_routes
from .schemas import (
    DeleteResponse,
    RoomResponse,
    ToggleResponse,
    Token,
    WhitelistCreate,
    WhitelistResponse,
    WhitelistUpdate,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_test_data()
    logger.info("Database initialized and seeded")
    yield


app = FastAPI(title="Internet EIN/AUS API", version="2.0.0", lifespan=lifespan)


@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response(status_code=200)
    else:
        response = await call_next(request)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "3600"

    return response


app.include_router(auth_routes.router)
app.include_router(room_routes.router)
app.include_router(whitelist_routes.router)

@app.put("/api/whitelists/{whitelist_id}", response_model=WhitelistResponse)
async def update_whitelist(
    whitelist_id: int,
    whitelist: WhitelistUpdate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    template = (
        db.query(WhitelistTemplate)
        .filter(WhitelistTemplate.id == whitelist_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Whitelist not found")

    room = db.query(Room).filter(Room.id == whitelist.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    template.name = whitelist.name
    template.urls = json.dumps(whitelist.urls)
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
        "urls": json.loads(template.urls),
        "room_id": template.room_id,
    }

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "internet-control-api", "version": "2.0.0"}
