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
    schedule_enabled: bool
    schedule_open_time: Optional[str]
    schedule_lock_time: Optional[str]
    manual_override_active: bool
    manual_override_enabled: Optional[bool]
    control_mode: str
    schedule_target_enabled: Optional[bool]

    class Config:
        from_attributes = True


class ToggleResponse(BaseModel):
    success: bool
    internet_enabled: bool
    room: str
    manual_override_active: bool
    control_mode: str


class RoomScheduleUpdate(BaseModel):
    schedule_enabled: bool
    schedule_open_time: Optional[str] = None
    schedule_lock_time: Optional[str] = None
    clear_override: bool = False

    @field_validator("schedule_open_time", "schedule_lock_time")
    @classmethod
    def validate_schedule_time(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        parts = value.split(":")
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            raise ValueError("Zeit muss im Format HH:MM angegeben werden")

        hour = int(parts[0])
        minute = int(parts[1])
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError("Ungültige Uhrzeit")

        return f"{hour:02d}:{minute:02d}"

    @field_validator("schedule_lock_time")
    @classmethod
    def validate_different_times(cls, value: Optional[str], info) -> Optional[str]:
        open_time = info.data.get("schedule_open_time")
        if open_time and value and open_time == value:
            raise ValueError("Öffnungs- und Sperrzeit dürfen nicht identisch sein")
        return value


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

    id: int
    timestamp: datetime
    username: str
    action: str
    target: Optional[str] = None
    detail: Optional[str] = None
    success: bool

    class Config:
        from_attributes = True


class WhitelistToggle(BaseModel):
    room_id: int
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
