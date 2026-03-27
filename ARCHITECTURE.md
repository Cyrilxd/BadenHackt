# Internet EIN/AUS - Container-Architektur

## System-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│                         INTERNET                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Firewall (extern)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              PERIMETER FIREWALL (Host)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Docker Compose Stack                           │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │ │
│  │  │   Frontend   │  │   Backend    │  │    Squid     │ │ │
│  │  │  (Nginx +    │  │  (FastAPI)   │  │ (URL-Filter) │ │ │
│  │  │  Vue.js/TS)  │  │              │  │              │ │ │
│  │  │  Port: 8080  │  │  Port: 8000  │  │  Port: 3128  │ │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │ │
│  │         │                 │                 │         │ │
│  │         └────────┬────────┴────────┬────────┘         │ │
│  │                  │                 │                  │ │
│  │         ┌────────▼─────────────────▼────────┐         │ │
│  │         │    SQLite DB (Volume)             │         │ │
│  │         │  - users                          │         │ │
│  │         │  - rooms                          │         │ │
│  │         │  - whitelist_templates            │         │ │
│  │         └───────────────────────────────────┘         │ │
│  └────────────────────────────────────────────────────────┘ │
│                       │                                      │
│  ┌────────────────────▼──────────────────────────────────┐  │
│  │  nftables (Host Network)                              │  │
│  │  - Rules per VLAN (Internet EIN/AUS)                  │  │
│  │  - Backend steuert via Docker Host-Access             │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬─────────────────┐
        │              │              │                 │
┌───────▼─────┐ ┌──────▼─────┐ ┌─────▼──────┐   ... (7 VLANs)
│  VLAN 18    │ │  VLAN 19   │ │  VLAN 20   │
│10.3.18.0/24 │ │10.3.19.0/24│ │10.3.20.0/24│
│ (Zimmer 1)  │ │ (Zimmer 2) │ │ (Zimmer 3) │
└─────────────┘ └────────────┘ └────────────┘
```

---

## Container-Details

### 1. Frontend (Nginx + Vue.js/TypeScript)

**Base:** `node:20-alpine` (Build) + `nginx:alpine` (Serve)

**Stack:**
- Vue 3 + TypeScript
- Vite (Build-Tool)
- Axios (HTTP-Client)
- TailwindCSS (Styling)

**Build-Prozess:**
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

**Routes:**
- `/` - Login
- `/dashboard` - Zimmer-Steuerung (Internet EIN/AUS)
- `/whitelist` - Whitelist-Manager

---

### 2. Backend (FastAPI + Python)

**Base:** `python:3.11-slim`

**Dependencies:**
- FastAPI (Web-Framework)
- Uvicorn (ASGI-Server)
- SQLAlchemy (ORM)
- python-jose (JWT)
- bcrypt (Password-Hashing)

**API-Endpoints:**
```
POST /api/login               → JWT-Token
GET  /api/rooms               → Liste (nur mein Zimmer)
POST /api/rooms/{id}/toggle   → Internet EIN/AUS
GET  /api/whitelists          → Templates
POST /api/whitelists          → Create/Upload
PUT  /api/whitelists/{id}     → Update
```

**nftables-Integration:**
```python
import subprocess

def block_vlan(vlan_subnet: str):
    subprocess.run([
        "docker", "exec", "host-network",
        "nft", "add", "rule", "inet", "filter", "forward",
        "ip", "saddr", vlan_subnet, "drop"
    ])
```

---

### 3. Squid (URL-Filtering)

**Base:** `sameersbn/squid:latest`

**Config (per VLAN):**
```squid
# /etc/squid/squid.conf
acl vlan18 src 10.3.18.0/24
acl vlan19 src 10.3.19.0/24

acl whitelist_vlan18 dstdomain .google.com .wikipedia.org
acl whitelist_vlan19 dstdomain .github.com .stackoverflow.com

http_access allow vlan18 whitelist_vlan18
http_access deny vlan18

http_access allow vlan19 whitelist_vlan19
http_access deny vlan19
```

**Backend updatet Config:**
- Template rendern (Jinja2)
- Config schreiben
- Squid reload: `docker exec squid squid -k reconfigure`

---

### 4. SQLite Database (Volume)

**Schema:**
```sql
users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,     -- "vlan18", "vlan19", ...
    password_hash TEXT,
    vlan_id INTEGER           -- 18, 19, 20, ...
)

rooms (
    id INTEGER PRIMARY KEY,
    name TEXT,                -- "Zimmer 1"
    subnet TEXT,              -- "10.3.18.0/24"
    vlan_id INTEGER,          -- 18
    internet_enabled BOOLEAN DEFAULT TRUE
)

whitelist_templates (
    id INTEGER PRIMARY KEY,
    name TEXT,                -- "Google Suite"
    urls TEXT,                -- JSON: ["google.com", "gmail.com"]
    room_id INTEGER REFERENCES rooms(id)
)
```

---

## Docker Compose

```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "8080:80"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data          # SQLite DB
      - /var/run/docker.sock:/var/run/docker.sock  # Host-Access
    privileged: true               # nftables-Zugriff
    network_mode: host             # Host-Netzwerk für nftables

  squid:
    image: sameersbn/squid:latest
    ports:
      - "3128:3128"
    volumes:
      - ./squid/squid.conf:/etc/squid/squid.conf
      - squid-cache:/var/spool/squid

volumes:
  squid-cache:
```

---

## User-Flow

### 1. Login
```
Lehrer → https://firewall:8080/
        → Eingabe: "vlan18" / "password"
        → Backend checkt DB
        → JWT-Token (enthält vlan_id)
        → Redirect zu /dashboard
```

### 2. Internet sperren
```
Dashboard → Button "Internet AUS" klicken
          → POST /api/rooms/18/toggle {"enabled": false}
          → Backend:
              1. nft add rule ... drop (VLAN 18 blockiert)
              2. DB-Update: internet_enabled = false
          → Frontend: Status-Update "🔴 Gesperrt"
```

### 3. Whitelist setzen
```
Whitelist-Manager → "Google Suite" Template wählen
                  → POST /api/whitelists {"urls": ["google.com", "gmail.com"]}
                  → Backend:
                      1. Squid-Config rendern
                      2. docker exec squid squid -k reconfigure
                  → Frontend: "✅ Whitelist aktiv"
```

---

## Deployment

**1. Build:**
```bash
cd /data/.openclaw/workspace/hackathon
docker-compose build
```

**2. Start:**
```bash
docker-compose up -d
```

**3. Init DB:**
```bash
docker exec backend python init_db.py
# Erstellt 7 User: vlan18, vlan19, ..., vlan119
```

**4. Access:**
```
Frontend: http://<server-ip>:8080
Backend API: http://<server-ip>:8000/docs
```

---

## Sicherheit

**JWT-Token:**
- Expiry: 8h
- Signed mit Secret-Key

**Passwords:**
- bcrypt-hashed (10 rounds)

**nftables-Isolation:**
- Backend läuft privileged, aber nur nftables-Commands erlaubt
- Keine Shell-Access von Containern

---

## Rollback

**Bei Problemen:**
```bash
docker-compose down
docker-compose up -d
```

**Alte Shorewall wieder aktivieren:**
- Container stoppen
- Alte Rules restaurieren

---

## Monitoring

**Container-Logs:**
```bash
docker-compose logs -f backend
docker-compose logs -f squid
```

**nftables-Status:**
```bash
nft list ruleset | grep forward
```

---

**Status:** Architektur definiert, ready to implement! 🦇
