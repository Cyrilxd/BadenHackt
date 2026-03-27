import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import auth, firewall
from .database import SessionLocal, get_db, init_db
from .init_data import init_test_data
from .room_schedule import sync_scheduled_rooms
from .routers import audit_routes, auth_routes, room_routes, whitelist_routes

ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _room_schedule_loop() -> None:
    while True:
        await asyncio.sleep(60)
        with SessionLocal() as db:
            try:
                sync_scheduled_rooms(db)
            except firewall.FirewallSyncError as exc:
                logger.warning("Scheduled firewall sync failed: %s", exc)
            except Exception:
                logger.exception("Timed room scheduler failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_test_data()
    logger.info("Database initialized and seeded")

    with SessionLocal() as db:
        try:
            sync_scheduled_rooms(db)
            firewall.FirewallManager.sync_all_rooms(db)
            logger.info("Initial firewall policy sync completed")
        except firewall.FirewallSyncError as exc:
            logger.warning("Initial firewall policy sync failed: %s", exc)

    scheduler_task = asyncio.create_task(_room_schedule_loop())

    yield

    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Internet EIN/AUS API", version="2.0.0", lifespan=lifespan)


@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response(status_code=200)
    else:
        response = await call_next(request)

    response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "3600"

    return response


app.include_router(auth_routes.router)
app.include_router(room_routes.router)
app.include_router(whitelist_routes.router)
app.include_router(audit_routes.router)


@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    ldap_status = "disabled"
    if auth.ldap_enabled():
        try:
            from ldap3 import NONE as LDAP_NONE
            from ldap3 import Connection, Server
            server = Server(auth._ldap_server_uri(), get_info=LDAP_NONE, connect_timeout=2)
            with Connection(server, auto_bind=True):
                ldap_status = "connected"
        except Exception:
            ldap_status = "error"

    all_ok = db_ok and ldap_status != "error"
    body = {
        "status": "ok" if all_ok else "degraded",
        "db": "connected" if db_ok else "error",
        "ldap": ldap_status,
        "service": "internet-control-api",
        "version": "2.0.0",
    }
    return JSONResponse(content=body, status_code=200 if all_ok else 503)
