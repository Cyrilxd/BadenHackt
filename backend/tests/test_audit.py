"""Tests für den Audit-Log-Service und die API."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.audit import AuditAction, log_action
from app.database import AuditLog, Base, get_db
from app.main import app

# --------------------------------------------------------------------------- #
# In-Memory SQLite für Tests                                                   #
# --------------------------------------------------------------------------- #

TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def db_session():
    engine = create_engine(
        TEST_DB_URL, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(db_session):
    """FastAPI-Testclient mit überschriebener DB-Session."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


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
    payload = json.loads(entry.detail)
    assert payload["enabled"] is True


def test_log_action_failed_login(db_session):
    """Fehlgeschlagener Login wird mit success=False protokolliert."""
    log_action(
        db_session,
        username="hacker",
        action=AuditAction.LOGIN_FAILED,
        success=False,
    )

    entry = (
        db_session.query(AuditLog)
        .filter_by(action="login_failed", username="hacker")
        .first()
    )
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

    entry = (
        db_session.query(AuditLog)
        .filter_by(action="whitelist_create", username="mueller")
        .first()
    )
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


def _get_token(client: TestClient) -> str:
    """Hilfe: Login-Token für Test-Nutzer holen."""
    resp = client.post(
        "/api/login",
        data={"username": "lehrer", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    # Wenn LDAP nicht läuft, ist 503 möglich — dann lokaler Fallback
    if resp.status_code == 503:
        pytest.skip("LDAP nicht erreichbar, Test übersprungen")
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_audit_endpoint_requires_auth(client):
    """Ohne JWT wird 401 zurückgegeben."""
    resp = client.get("/api/audit")
    assert resp.status_code == 401


def test_audit_endpoint_returns_list(client):
    """Mit gültigem JWT gibt /api/audit eine Liste zurück."""
    token = _get_token(client)
    resp = client.get(
        "/api/audit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # Mindestens die Einträge aus den unit tests oben
    assert len(data) >= 1


def test_audit_endpoint_filter_by_action(client):
    """Filter nach action funktioniert."""
    token = _get_token(client)
    resp = client.get(
        "/api/audit?action=internet_toggle",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    for entry in resp.json():
        assert entry["action"] == "internet_toggle"


def test_audit_endpoint_filter_by_success(client):
    """Filter nach success=false liefert nur fehlgeschlagene Einträge."""
    token = _get_token(client)
    resp = client.get(
        "/api/audit?success=false",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    for entry in resp.json():
        assert entry["success"] is False


def test_audit_endpoint_limit(client):
    """limit-Parameter wird eingehalten."""
    token = _get_token(client)
    resp = client.get(
        "/api/audit?limit=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) <= 2


def test_audit_entry_schema(client):
    """Jeder Eintrag enthält alle erwarteten Felder."""
    token = _get_token(client)
    resp = client.get(
        "/api/audit?limit=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    entries = resp.json()
    if entries:
        entry = entries[0]
        for field in ("id", "timestamp", "username", "action", "success"):
            assert field in entry, f"Feld '{field}' fehlt im Audit-Eintrag"
