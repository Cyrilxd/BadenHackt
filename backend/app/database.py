import json
import os
from typing import List

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/internet_control.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    vlan_id = Column(Integer, default=0)
    room_name = Column(String)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subnet = Column(String, nullable=False)
    vlan_id = Column(Integer, unique=True, nullable=False)
    internet_enabled = Column(Boolean, default=True, nullable=False)

    whitelists = relationship(
        "WhitelistTemplate",
        back_populates="room",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Room {self.name} (VLAN {self.vlan_id})>"


class WhitelistTemplate(Base):
    __tablename__ = "whitelist_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    urls = Column(Text, nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)

    room = relationship("Room", back_populates="whitelists")

    @property
    def url_list(self) -> List[str]:
        if not self.urls:
            return []
        return json.loads(self.urls)

    @url_list.setter
    def url_list(self, value: List[str]) -> None:
        self.urls = json.dumps(value)

    def __repr__(self) -> str:
        return f"<WhitelistTemplate {self.name} (room_id={self.room_id})>"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
