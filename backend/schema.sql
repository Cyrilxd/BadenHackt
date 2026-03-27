PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    vlan_id INTEGER DEFAULT 0,
    room_name TEXT
);

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subnet TEXT NOT NULL,
    vlan_id INTEGER UNIQUE NOT NULL,
    internet_enabled BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS whitelist_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    urls TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS room_whitelist_assignments (
    room_id INTEGER NOT NULL,
    whitelist_id INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 0,
    PRIMARY KEY (room_id, whitelist_id),
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (whitelist_id) REFERENCES whitelist_templates(id) ON DELETE CASCADE
);
