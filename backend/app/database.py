import json
import os
from typing import List

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
    text,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/internet_control.db")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


if IS_SQLITE:

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


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
    room_id = Column(
        Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False
    )

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


def _sqlite_whitelist_table_needs_migration(connection) -> bool:
    table_exists = connection.execute(
        text(
            "SELECT 1 FROM sqlite_master "
            "WHERE type = 'table' AND name = 'whitelist_templates'"
        )
    ).scalar_one_or_none()
    if not table_exists:
        return False

    columns = {
        row["name"]: row
        for row in connection.execute(
            text("PRAGMA table_info(whitelist_templates)")
        ).mappings()
    }
    foreign_keys = list(
        connection.execute(
            text("PRAGMA foreign_key_list(whitelist_templates)")
        ).mappings()
    )

    room_id = columns.get("room_id")
    has_room_fk = any(
        fk["table"] == "rooms"
        and fk["from"] == "room_id"
        and fk["to"] == "id"
        and fk["on_delete"].upper() == "CASCADE"
        for fk in foreign_keys
    )

    return room_id is None or room_id["notnull"] != 1 or not has_room_fk


def _migrate_sqlite_whitelist_table() -> None:
    with engine.begin() as connection:
        if not _sqlite_whitelist_table_needs_migration(connection):
            return

        columns = [
            row["name"]
            for row in connection.execute(
                text("PRAGMA table_info(whitelist_templates)")
            ).mappings()
        ]
        row_count = connection.execute(
            text("SELECT COUNT(*) FROM whitelist_templates")
        ).scalar_one()

        if "room_id" not in columns and row_count:
            raise RuntimeError(
                "Cannot auto-migrate existing whitelist_templates rows without room_id. "
                "Delete or manually map legacy whitelist entries first."
            )

        if "room_id" in columns:
            null_room_count = connection.execute(
                text("SELECT COUNT(*) FROM whitelist_templates WHERE room_id IS NULL")
            ).scalar_one()
            if null_room_count:
                raise RuntimeError(
                    "Cannot auto-migrate whitelist_templates rows with NULL room_id. "
                    "Assign each legacy whitelist to a room first."
                )

        connection.execute(
            text("ALTER TABLE whitelist_templates RENAME TO whitelist_templates_legacy")
        )
        connection.execute(
            text(
                """
                CREATE TABLE whitelist_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    urls TEXT NOT NULL,
                    room_id INTEGER NOT NULL,
                    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO whitelist_templates (id, name, urls, room_id)
                SELECT id, name, urls, room_id
                FROM whitelist_templates_legacy
                """
            )
        )
        connection.execute(text("DROP TABLE whitelist_templates_legacy"))


def init_db():
    if IS_SQLITE:
        _migrate_sqlite_whitelist_table()
    Base.metadata.create_all(bind=engine)
