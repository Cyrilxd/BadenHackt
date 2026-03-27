import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

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


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subnet = Column(String, nullable=False)
    vlan_id = Column(Integer, unique=True, nullable=False)
    internet_enabled = Column(Boolean, default=True, nullable=False)


class WhitelistTemplate(Base):
    __tablename__ = "whitelist_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    urls = Column(Text, nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
