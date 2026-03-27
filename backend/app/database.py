import json
import os
from datetime import datetime, timezone
from typing import List

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
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

    whitelist_assignments = relationship(
        "RoomWhitelistAssignment",
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
    assignments = relationship(
        "RoomWhitelistAssignment",
        back_populates="whitelist",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def url_list(self) -> List[str]:
        if not self.urls:
            return []
        return json.loads(self.urls)

    @url_list.setter
    def url_list(self, value: List[str]) -> None:
        self.urls = json.dumps(value)

    def __repr__(self) -> str:
        return f"<WhitelistTemplate {self.name}>"


class RoomWhitelistAssignment(Base):
    __tablename__ = "room_whitelist_assignments"

    room_id = Column(
        Integer, ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True
    )
    whitelist_id = Column(
        Integer,
        ForeignKey("whitelist_templates.id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_active = Column(Boolean, default=False, nullable=False)

    room = relationship("Room", back_populates="whitelist_assignments")
    whitelist = relationship("WhitelistTemplate", back_populates="assignments")

    def __repr__(self) -> str:
        return (
            f"<RoomWhitelistAssignment room_id={self.room_id} "
            f"whitelist_id={self.whitelist_id} active={self.is_active}>"
        )


class AuditLog(Base):
    """Persistentes Protokoll aller sicherheitsrelevanten Aktionen."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    username = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    target = Column(String, nullable=True)  # z. B. "Zimmer 2 (VLAN 19)"
    detail = Column(Text, nullable=True)  # JSON-String mit Zusatzinfos
    success = Column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return (
            f"<AuditLog {self.action} by {self.username} "
            f"@ {self.timestamp} success={self.success}>"
        )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _sqlite_whitelist_table_needs_migration(connection) -> bool:
    templates_exists = connection.execute(
        text(
            "SELECT 1 FROM sqlite_master "
            "WHERE type = 'table' AND name = 'whitelist_templates'"
        )
    ).scalar_one_or_none()
    assignments_exists = connection.execute(
        text(
            "SELECT 1 FROM sqlite_master "
            "WHERE type = 'table' AND name = 'room_whitelist_assignments'"
        )
    ).scalar_one_or_none()

    if not templates_exists:
        return False
    if not assignments_exists:
        return True

    columns = {
        row["name"]: row
        for row in connection.execute(
            text("PRAGMA table_info(whitelist_templates)")
        ).mappings()
    }
    assignment_columns = {
        row["name"]: row
        for row in connection.execute(
            text("PRAGMA table_info(room_whitelist_assignments)")
        ).mappings()
    }
    assignment_fks = list(
        connection.execute(
            text("PRAGMA foreign_key_list(room_whitelist_assignments)")
        ).mappings()
    )

    has_template_room_id = "room_id" in columns
    has_assignment_room_id = assignment_columns.get("room_id") is not None
    has_assignment_whitelist_id = assignment_columns.get("whitelist_id") is not None
    has_assignment_is_active = (
        assignment_columns.get("is_active") is not None
        and assignment_columns["is_active"]["notnull"] == 1
    )
    has_room_fk = any(
        fk["table"] == "rooms"
        and fk["from"] == "room_id"
        and fk["to"] == "id"
        and fk["on_delete"].upper() == "CASCADE"
        for fk in assignment_fks
    )
    has_whitelist_fk = any(
        fk["table"] == "whitelist_templates"
        and fk["from"] == "whitelist_id"
        and fk["to"] == "id"
        and fk["on_delete"].upper() == "CASCADE"
        for fk in assignment_fks
    )

    return (
        has_template_room_id
        or not has_assignment_room_id
        or not has_assignment_whitelist_id
        or not has_assignment_is_active
        or not has_room_fk
        or not has_whitelist_fk
    )


def _migrate_sqlite_whitelist_table() -> None:
    with engine.begin() as connection:
        if not _sqlite_whitelist_table_needs_migration(connection):
            return

        assignments_exists = connection.execute(
            text(
                "SELECT 1 FROM sqlite_master "
                "WHERE type = 'table' AND name = 'room_whitelist_assignments'"
            )
        ).scalar_one_or_none()
        columns = [
            row["name"]
            for row in connection.execute(
                text("PRAGMA table_info(whitelist_templates)")
            ).mappings()
        ]
        if "room_id" in columns:
            row_count = connection.execute(
                text("SELECT COUNT(*) FROM whitelist_templates")
            ).scalar_one()
            if row_count:
                null_room_count = connection.execute(
                    text(
                        "SELECT COUNT(*) FROM whitelist_templates WHERE room_id IS NULL"
                    )
                ).scalar_one()
                if null_room_count:
                    raise RuntimeError(
                        "Cannot auto-migrate whitelist_templates rows with NULL room_id. "
                        "Assign each legacy whitelist to a room first."
                    )

            connection.execute(
                text(
                    "ALTER TABLE whitelist_templates RENAME TO whitelist_templates_legacy"
                )
            )
            connection.execute(
                text(
                    """
                    CREATE TABLE whitelist_templates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        urls TEXT NOT NULL
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    CREATE TABLE room_whitelist_assignments (
                        room_id INTEGER NOT NULL,
                        whitelist_id INTEGER NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT 0,
                        PRIMARY KEY (room_id, whitelist_id),
                        FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                        FOREIGN KEY (whitelist_id) REFERENCES whitelist_templates(id) ON DELETE CASCADE
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO whitelist_templates (id, name, urls)
                    SELECT id, name, urls
                    FROM whitelist_templates_legacy
                    """
                )
            )
            if "is_active" in columns:
                connection.execute(
                    text(
                        """
                        INSERT INTO room_whitelist_assignments (room_id, whitelist_id, is_active)
                        SELECT room_id, id, COALESCE(is_active, 1)
                        FROM whitelist_templates_legacy
                        """
                    )
                )
            else:
                connection.execute(
                    text(
                        """
                        INSERT INTO room_whitelist_assignments (room_id, whitelist_id, is_active)
                        SELECT room_id, id, 1
                        FROM whitelist_templates_legacy
                        """
                    )
                )
            connection.execute(text("DROP TABLE whitelist_templates_legacy"))
            return

        if assignments_exists:
            connection.execute(text("DROP TABLE room_whitelist_assignments"))
        connection.execute(
            text(
                """
                CREATE TABLE room_whitelist_assignments (
                    room_id INTEGER NOT NULL,
                    whitelist_id INTEGER NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 0,
                    PRIMARY KEY (room_id, whitelist_id),
                    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                    FOREIGN KEY (whitelist_id) REFERENCES whitelist_templates(id) ON DELETE CASCADE
                )
                """
            )
        )


def init_db():
    if IS_SQLITE:
        _migrate_sqlite_whitelist_table()
    Base.metadata.create_all(bind=engine)
