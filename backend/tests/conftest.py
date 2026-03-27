"""Shared pytest fixtures for API integration tests.

Strategy:
- In-memory SQLite with StaticPool so all connections share one DB.
- Override the FastAPI `get_db` dependency per test with an isolated session.
- Mock lifespan side-effects (init_test_data, firewall sync) so tests never
  need a real firewall agent or pre-seeded data.
"""
import os

# Must be set BEFORE any app module is imported so that database.py and
# auth.py read these values when their module-level code executes.
os.environ.setdefault("AUTH_MODE", "local")
os.environ.setdefault("SECRET_KEY", "pytest-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db, User, Room
from app import auth
from app.main import app


def _make_test_engine():
    """In-memory SQLite engine; StaticPool ensures one shared connection."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


@pytest.fixture()
def db():
    """Isolated in-memory database — created fresh and torn down per test."""
    engine = _make_test_engine()
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    """FastAPI TestClient with test DB and mocked startup side-effects."""

    def _override_db():
        yield db

    app.dependency_overrides[get_db] = _override_db

    with (
        patch("app.main.init_test_data"),
        patch("app.firewall.FirewallManager.sync_all_rooms"),
        patch("app.firewall.FirewallManager.sync_room_policies"),
    ):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Domain fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def room(db) -> Room:
    """A single test room, ready in the DB."""
    r = Room(name="Zimmer 1", subnet="10.3.18.0/24", vlan_id=18, internet_enabled=True)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@pytest.fixture()
def user(db) -> User:
    """A local test user, ready in the DB."""
    u = User(
        username="testlehrer",
        password_hash=auth.get_password_hash("test123"),
        vlan_id=0,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def auth_headers(user) -> dict:
    """Authorization header with a valid JWT for the test user."""
    token = auth.create_access_token(
        data={"sub": user.username, "auth_source": "local"}
    )
    return {"Authorization": f"Bearer {token}"}
