import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import auth
from ..database import get_db
from ..schemas import Token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = None
    auth_source = "local"

    if auth.ldap_enabled():
        try:
            user = auth.authenticate_ldap_user(form_data.username, form_data.password)
            if user:
                auth_source = "ldap"
        except Exception as exc:
            logger.exception("LDAP authentication failed for %s", form_data.username)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LDAP authentication service unavailable",
            ) from exc

    if not user and auth.get_auth_mode() != "ldap":
        user = auth.authenticate_local_user(form_data.username, form_data.password, db)
        auth_source = "local"

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(
        data={"sub": user.username, "auth_source": auth_source}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"username": user.username, "role": "teacher"},
    }
