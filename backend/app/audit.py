"""
Audit-Log: Persistente Protokollierung aller sicherheitsrelevanten Aktionen.

Verwendung in Routen:
    from ..audit import AuditAction, log_action
    log_action(db, username=current_user.username, action=AuditAction.INTERNET_TOGGLE, ...)
"""

from __future__ import annotations

import json
import logging
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Typsichere Aktionsnamen – keine Freitextstrings in den Routen."""
    LOGIN_SUCCESS      = "login_success"
    LOGIN_FAILED       = "login_failed"
    INTERNET_TOGGLE    = "internet_toggle"
    WHITELIST_CREATE   = "whitelist_create"
    WHITELIST_UPDATE   = "whitelist_update"
    WHITELIST_DELETE   = "whitelist_delete"
    WHITELIST_TOGGLE   = "whitelist_toggle"


def log_action(
    db: Session,
    *,
    username: str,
    action: AuditAction,
    target: str | None = None,
    detail: dict[str, Any] | None = None,
    success: bool = True,
) -> None:
    """
    Schreibt einen Audit-Eintrag in die Datenbank.

    Wird NACH dem DB-Commit der eigentlichen Aktion aufgerufen damit kein
    Eintrag entsteht wenn die Hauptaktion fehlschlägt (Firewall-Fehler etc.).
    Bei Login-Ereignissen auch bei Fehler aufrufen (success=False).
    """
    # Import hier damit kein zirkulärer Import entsteht
    from .database import AuditLog

    entry = AuditLog(
        username=username,
        action=action.value,
        target=target,
        detail=json.dumps(detail, ensure_ascii=False) if detail else None,
        success=success,
    )
    db.add(entry)

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.warning(
            "Audit-Log konnte nicht geschrieben werden: action=%s user=%s",
            action.value,
            username,
        )
