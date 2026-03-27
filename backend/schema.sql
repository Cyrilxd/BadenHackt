CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    vlan_id INTEGER,
    room_name TEXT
);

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subnet TEXT NOT NULL,
    vlan_id INTEGER UNIQUE,
    internet_enabled BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS whitelist_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    urls TEXT NOT NULL,
    room_id INTEGER,
    FOREIGN KEY(room_id) REFERENCES rooms(id)
);
