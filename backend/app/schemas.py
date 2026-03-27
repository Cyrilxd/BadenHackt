from typing import List
from urllib.parse import urlsplit

from pydantic import BaseModel, field_validator


def _normalize_whitelist_entry(raw_value: str) -> str:
    value = raw_value.strip().lower()
    if not value:
        return ""

    if "://" in value:
        parsed = urlsplit(value)
        value = parsed.hostname or ""
    else:
        value = value.split("/", 1)[0]
        if "@" in value:
            value = value.rsplit("@", 1)[-1]
        if value.count(":") == 1:
            host, port = value.rsplit(":", 1)
            if port.isdigit():
                value = host

    value = value.strip().rstrip(".")
    if value.startswith("*."):
        value = value[2:]

    return value


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

    @field_validator("urls")
    @classmethod
    def clean_urls(cls, v: List[str]) -> List[str]:
        cleaned: List[str] = []
        seen: set[str] = set()
        for url in v:
            normalized = _normalize_whitelist_entry(url)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            cleaned.append(normalized)
        if not cleaned:
            raise ValueError("Mindestens eine URL erforderlich")
        return cleaned


class WhitelistResponse(BaseModel):
    id: int
    name: str
    urls: List[str]
    room_id: int

    class Config:
        from_attributes = True


class DeleteResponse(BaseModel):
    success: bool


class WhitelistUpdate(BaseModel):
    name: str
    urls: List[str]
    room_id: int

    @field_validator("urls")
    @classmethod
    def clean_urls(cls, v: List[str]) -> List[str]:
        cleaned: List[str] = []
        seen: set[str] = set()
        for url in v:
            normalized = _normalize_whitelist_entry(url)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            cleaned.append(normalized)
        if not cleaned:
            raise ValueError("Mindestens eine URL erforderlich")
        return cleaned
