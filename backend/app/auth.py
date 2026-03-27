import hashlib
import hmac
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from ldap3 import ALL, Connection, Server
from ldap3.utils.conv import escape_filter_chars
from sqlalchemy.orm import Session

from . import database

SECRET_KEY = os.environ.get("SECRET_KEY", "hackathon-2026-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")


@dataclass
class AuthenticatedUser:
    username: str
    role: str = "teacher"
    auth_source: str = "local"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return hmac.compare_digest(password_hash, hashed_password)


def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def get_auth_mode() -> str:
    return os.environ.get("AUTH_MODE", "local").strip().lower()


def ldap_enabled() -> bool:
    return get_auth_mode() in {"ldap", "auto"}


def _ldap_server_uri() -> str:
    return os.environ.get("LDAP_SERVER_URI") or (
        f"ldap://{os.environ.get('LDAP_HOST', 'ldap')}:{os.environ.get('LDAP_PORT', '389')}"
    )


def _ldap_server() -> Server:
    return Server(_ldap_server_uri(), get_info=ALL)


def _ldap_bind_and_search(username: str) -> Optional[str]:
    bind_dn = os.environ.get("LDAP_BIND_DN")
    bind_password = os.environ.get("LDAP_BIND_PASSWORD")
    search_base = os.environ.get("LDAP_USER_SEARCH_BASE") or os.environ.get(
        "LDAP_BASE_DN"
    )
    search_filter = os.environ.get(
        "LDAP_USER_SEARCH_FILTER", "(uid={username})"
    ).format(username=escape_filter_chars(username))

    if not bind_dn or bind_password is None or not search_base:
        return None

    with Connection(
        _ldap_server(), user=bind_dn, password=bind_password, auto_bind=True
    ) as conn:
        conn.search(
            search_base=search_base, search_filter=search_filter, attributes=["uid"]
        )
        if not conn.entries:
            return None
        return conn.entries[0].entry_dn


def authenticate_ldap_user(username: str, password: str) -> Optional[AuthenticatedUser]:
    if not ldap_enabled():
        return None

    try:
        user_dn = _ldap_bind_and_search(username)
        if not user_dn:
            return None

        with Connection(
            _ldap_server(), user=user_dn, password=password, auto_bind=True
        ):
            return AuthenticatedUser(username=username, auth_source="ldap")
    except Exception:
        if get_auth_mode() == "ldap":
            raise
        return None


def authenticate_local_user(
    username: str, password: str, db: Session
) -> Optional[database.User]:
    user = db.query(database.User).filter(database.User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        auth_source: str = payload.get("auth_source", "local")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if auth_source == "ldap":
        return AuthenticatedUser(username=username, auth_source="ldap")

    user = db.query(database.User).filter(database.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
