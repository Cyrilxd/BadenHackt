"""Tests für den Audit-Log-Service und die API."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.audit import AuditAction, log_action
from app.auth import create_access_token, get_password_hash
from app.database import AuditLog, Base, User, get_db
from app.main import app

# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def db_session():
    """
    In-Memory SQLite mit StaticPool: alle Verbindungen teilen dieselbe
    Datenbank-Instanz — Pflicht für :memory: damit Tabellen nicht verloren gehen.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Testnutzer seeden damit JWT-Auth in API-Tests funktioniert
    session.add(User(
        username="lehrer",
        password_hash=get_password_hash("admin123"),
        vlan_id=0,
        room_name="Test Lehrer",
    ))
    session.commit()

    yield session
    session.close()


@pytest.fixture(scope="module")
def client(db_session):
    """FastAPI-Testclient mit überschriebener DB-Session."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def auth_header():
    """
    JWT direkt erzeugen — kein Roundtrip über den Login-Endpunkt nötig.
    Testet auth-unabhängig die Audit-API.
    """
    token = create_access_token(data={"sub": "lehrer", "auth_source": "local"})
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------- #
# Unit-Tests: log_action()                                                     #
# --------------------------------------------------------------------------- #

def test_log_action_creates_entry(db_session):
    """log_action schreibt einen Eintrag in audit_logs."""
    log_action(
        db_session,
        username="lehrer",
        action=AuditAction.INTERNET_TOGGLE,
        target="Zimmer 1 (VLAN 18)",
        detail={"enabled": True},
    )
    entry = db_session.query(AuditLog).filter_by(action="internet_toggle").first()
    assert entry is not None
    assert entry.username == "lehrer"
    assert entry.target == "Zimmer 1 (VLAN 18)"
    assert entry.success is True
    assert json.loads(entry.detail)["enabled"] is True


def test_log_action_failed_login(db_session):
    """Fehlgeschlagener Login wird mit success=False protokolliert."""
    log_action(db_session, username="hacker", action=AuditAction.LOGIN_FAILED, success=False)
    entry = db_session.query(AuditLog).filter_by(action="login_failed", username="hacker").first()
    assert entry is not None
    assert entry.success is False
    assert entry.detail is None


def test_log_action_whitelist_create(db_session):
    """Whitelist-Erstellung wird korrekt protokolliert."""
    log_action(
        db_session,
        username="mueller",
        action=AuditAction.WHITELIST_CREATE,
        target="Mathe-Portale → Zimmer 3",
        detail={"urls": ["khan-academy.org"], "active": True},
    )
    entry = db_session.query(AuditLog).filter_by(action="whitelist_create", username="mueller").first()
    assert entry is not None
    assert "Mathe-Portale" in entry.target


def test_log_action_all_enum_values_are_strings():
    """Alle AuditAction-Werte sind gültige Strings (keine int-Enums)."""
    for action in AuditAction:
        assert isinstance(action.value, str)
        assert len(action.value) > 0


# --------------------------------------------------------------------------- #
# API-Tests: GET /api/audit                                                    #
# --------------------------------------------------------------------------- #

def test_audit_endpoint_requires_auth(client):
    """Ohne JWT wird 401 zurückgegeben."""
    assert client.get("/api/audit").status_code == 401


def test_audit_endpoint_returns_list(client, auth_header):
    """Mit gültigem JWT gibt /api/audit eine Liste zurück."""
    resp = client.get("/api/audit", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # mindestens die Einträge aus den Unit-Tests


def test_audit_endpoint_filter_by_action(client, auth_header):
    """Filter nach action gibt nur passende Einträge zurück."""
    resp = client.get("/api/audit?action=internet_toggle", headers=auth_header)
    assert resp.status_code == 200
    for entry in resp.json():
        assert entry["action"] == "internet_toggle"


def test_audit_endpoint_filter_by_success(client, auth_header):
    """Filter success=false liefert nur fehlgeschlagene Einträge."""
    resp = client.get("/api/audit?success=false", headers=auth_header)
    assert resp.status_code == 200
    for entry in resp.json():
        assert entry["success"] is False


def test_audit_endpoint_limit(client, auth_header):
    """limit-Parameter wird eingehalten."""
    resp = client.get("/api/audit?limit=2", headers=auth_header)
    assert resp.status_code == 200
    assert len(resp.json()) <= 2


def test_audit_entry_schema(client, auth_header):
    """Jeder Eintrag enthält alle erwarteten Felder."""
    resp = client.get("/api/audit?limit=1", headers=auth_header)
    assert resp.status_code == 200
    entries = resp.json()
    if entries:
        for field in ("id", "timestamp", "username", "action", "success"):
            assert field in entries[0], f"Feld '{field}' fehlt im Audit-Eintrag"
