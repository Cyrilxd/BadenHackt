CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'teacher'
);

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subnet TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS whitelist_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    urls TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER,
    day_of_week INTEGER,
    start_time TEXT,
    end_time TEXT,
    action TEXT,
    FOREIGN KEY(room_id) REFERENCES rooms(id)
);

CREATE TABLE IF NOT EXISTS room_status (
    room_id INTEGER PRIMARY KEY,
    internet_enabled BOOLEAN DEFAULT 1,
    active_whitelist INTEGER,
    FOREIGN KEY(room_id) REFERENCES rooms(id),
    FOREIGN KEY(active_whitelist) REFERENCES whitelist_templates(id)
);
