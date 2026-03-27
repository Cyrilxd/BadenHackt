import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from . import firewall
from .database import SessionLocal, init_db
from .init_data import init_test_data
from .room_schedule import sync_scheduled_rooms
from .routers import audit_routes, auth_routes, room_routes, whitelist_routes

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

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "3600"

    return response


app.include_router(auth_routes.router)
app.include_router(room_routes.router)
app.include_router(whitelist_routes.router)
app.include_router(audit_routes.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "internet-control-api", "version": "2.0.0"}
