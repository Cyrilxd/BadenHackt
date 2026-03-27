"""Initialize database with test data for 7 rooms"""
from sqlalchemy.orm import Session
from .database import engine, SessionLocal, User, Room, init_db
from .auth import get_password_hash

ROOMS = [
    {"vlan_id": 18, "subnet": "10.3.18.0/24", "name": "Zimmer 1"},
    {"vlan_id": 19, "subnet": "10.3.19.0/24", "name": "Zimmer 2"},
    {"vlan_id": 20, "subnet": "10.3.20.0/24", "name": "Zimmer 3"},
    {"vlan_id": 21, "subnet": "10.3.21.0/24", "name": "Zimmer 4"},
    {"vlan_id": 22, "subnet": "10.3.22.0/24", "name": "Zimmer 5"},
    {"vlan_id": 118, "subnet": "10.3.118.0/24", "name": "Zimmer 6"},
    {"vlan_id": 119, "subnet": "10.3.119.0/24", "name": "Zimmer 7"},
]

DEFAULT_PASSWORD = "admin123"

def init_test_data():
    """Create rooms and users for testing"""
    init_db()
    db = SessionLocal()
    
    try:
        # Create rooms
        for room_data in ROOMS:
            existing_room = db.query(Room).filter(Room.vlan_id == room_data["vlan_id"]).first()
            if not existing_room:
                room = Room(
                    name=room_data["name"],
                    subnet=room_data["subnet"],
                    vlan_id=room_data["vlan_id"],
                    internet_enabled=True
                )
                db.add(room)
                print(f"✅ Created room: {room_data['name']} (VLAN {room_data['vlan_id']})")
        
        db.commit()
        
        # Create users (one admin per room)
        for room_data in ROOMS:
            username = f"vlan{room_data['vlan_id']}"
            existing_user = db.query(User).filter(User.username == username).first()
            
            if not existing_user:
                user = User(
                    username=username,
                    password_hash=get_password_hash(DEFAULT_PASSWORD),
                    vlan_id=room_data["vlan_id"],
                    room_name=room_data["name"]
                )
                db.add(user)
                print(f"✅ Created user: {username} (password: {DEFAULT_PASSWORD})")
        
        db.commit()
        
        print("\n🎉 Database initialized successfully!")
        print("\n📋 Test Logins:")
        print("="*50)
        for room_data in ROOMS:
            print(f"  Username: vlan{room_data['vlan_id']:<3} | Password: {DEFAULT_PASSWORD} | {room_data['name']}")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Error initializing data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_test_data()
