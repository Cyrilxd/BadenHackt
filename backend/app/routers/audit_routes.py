"""
Audit-Log API-Endpunkte.

GET /api/audit  — Liste der letzten Einträge (JWT-geschützt, max. 200).
Filter via Query-Parameter: username, action, success, limit.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import auth
from ..database import AuditLog, User, get_db
from ..schemas import AuditLogResponse

router = APIRouter(prefix="/api", tags=["audit"])


@router.get("/audit", response_model=list[AuditLogResponse])
async def get_audit_logs(
    username:    Optional[str]  = Query(None, description="Filtern nach Benutzer"),
    action:      Optional[str]  = Query(None, description="Filtern nach Aktionstyp"),
    success:     Optional[bool] = Query(None, description="Nur erfolgreiche oder fehlgeschlagene Einträge"),
    limit:       int            = Query(100, ge=1, le=200, description="Max. Anzahl Einträge"),
    current_user: User          = Depends(auth.get_current_user),
    db:           Session       = Depends(get_db),
):
    """
    Gibt Audit-Log-Einträge zurück, neueste zuerst.
    Alle angemeldeten Lehrer können das Log einsehen.
    """
    query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())

    if username is not None:
        query = query.filter(AuditLog.username == username)
    if action is not None:
        query = query.filter(AuditLog.action == action)
    if success is not None:
        query = query.filter(AuditLog.success == success)

    return query.limit(limit).all()
