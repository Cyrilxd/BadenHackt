from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator

from .validators import parse_whitelist_url_entry


class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict


class RoomResponse(BaseModel):
    id: int
    name: str
    subnet: str
    vlan_id: int
    internet_enabled: bool

    class Config:
        from_attributes = True


class ToggleResponse(BaseModel):
    success: bool
    internet_enabled: bool
    room: str


class WhitelistCreate(BaseModel):
    name: str
    urls: List[str]
    room_id: int
    is_active: bool = True

    @field_validator("urls")
    @classmethod
    def clean_urls(cls, v: List[str]) -> List[str]:
        cleaned: List[str] = []
        seen: set[str] = set()
        for url in v:
            canonical = parse_whitelist_url_entry(url)
            if canonical is None or canonical in seen:
                continue
            seen.add(canonical)
            cleaned.append(canonical)
        if not cleaned:
            raise ValueError("Mindestens eine URL erforderlich")
        return cleaned


class WhitelistResponse(BaseModel):
    id: int
    name: str
    urls: List[str]
    room_id: int
    is_active: bool

    class Config:
        from_attributes = True


class DeleteResponse(BaseModel):
    success: bool


class AuditLogResponse(BaseModel):
    """Einzelner Audit-Eintrag für API-Antworten."""

    id:        int
    timestamp: datetime
    username:  str
    action:    str
    target:    Optional[str] = None
    detail:    Optional[str] = None
    success:   bool

    class Config:
        from_attributes = True


class WhitelistToggle(BaseModel):
    is_active: bool

class WhitelistUpdate(BaseModel):
    name: str
    urls: List[str]
    room_id: int
    is_active: bool = True

    @field_validator("urls")
    @classmethod
    def clean_urls(cls, v: List[str]) -> List[str]:
        cleaned: List[str] = []
        seen: set[str] = set()
        for url in v:
            canonical = parse_whitelist_url_entry(url)
            if canonical is None or canonical in seen:
                continue
            seen.add(canonical)
            cleaned.append(canonical)
        if not cleaned:
            raise ValueError("Mindestens eine URL erforderlich")
        return cleaned
