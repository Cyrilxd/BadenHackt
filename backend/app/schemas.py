from pydantic import BaseModel, field_validator
from typing import List


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
        cleaned = [url.strip() for url in v if url.strip()]
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
