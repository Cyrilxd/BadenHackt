from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/internet_control.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    vlan_id = Column(Integer)  # 18, 19, 20, 21, 22, 118, 119
    room_name = Column(String)  # "Zimmer 1", "Zimmer 2", etc.

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    subnet = Column(String)  # "10.3.18.0/24"
    vlan_id = Column(Integer, unique=True)
    internet_enabled = Column(Boolean, default=True)

class WhitelistTemplate(Base):
    __tablename__ = "whitelist_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    urls = Column(Text)  # JSON array as string
    room_id = Column(Integer, ForeignKey("rooms.id"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
