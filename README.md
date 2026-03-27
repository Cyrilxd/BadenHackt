# Internet EIN/AUS - Schulzimmer-Kontrolle

Hackathon Challenge für zB. Zentrum Bildung Baden

## Features

- ✅ **Alle Lehrer können ALLE 7 Zimmer steuern** (Multi-Room Dashboard)
- ✅ Internet EIN/AUS pro Schulzimmer (7 VLANs)
- ✅ URL-Whitelist-Management **PRO ZIMMER**
- ✅ Modernes Vue 3 + TypeScript Frontend
- ✅ FastAPI Backend mit JWT-Auth
- ✅ nftables Firewall-Integration
- ✅ Docker Compose Deployment
- 🔜 LDAP-Integration (optional)

## Architektur

```
Internet → Firewall → Perimeter Firewall (Docker) → 7 VLANs
                     ├── Frontend (Nginx + Vue 3 + TypeScript)
                     ├── Backend (FastAPI + nftables)
                     └── SQLite (User + Rooms + Whitelists)
```

**Visualisierung:** Siehe `architecture.html` für interaktive Grafik

## User-Konzept

- **Jeder Lehrer** kann sich einloggen
- **Jeder sieht alle 7 Zimmer** im Dashboard
- **Jeder kann jedes Zimmer** steuern (Internet EIN/AUS)
- **Whitelists sind pro Zimmer** (nicht pro User)

## Setup

### 1. Init Database

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.init_data
```

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Access

- **Frontend:** http://localhost:8080
- **Backend API:** http://localhost:8000/docs

## Test-Logins

**Alle User können ALLE Zimmer steuern:**

| Username | Password | Beschreibung |
|----------|----------|--------------|
| lehrer   | admin123 | Test Lehrer  |
| mueller  | admin123 | Herr Müller  |
| schmidt  | admin123 | Frau Schmidt |

## Schulzimmer (VLANs)

| Zimmer | VLAN | Subnetz |
|--------|------|---------|
| Zimmer 1 | 18  | 10.3.18.0/24 |
| Zimmer 2 | 19  | 10.3.19.0/24 |
| Zimmer 3 | 20  | 10.3.20.0/24 |
| Zimmer 4 | 21  | 10.3.21.0/24 |
| Zimmer 5 | 22  | 10.3.22.0/24 |
| Zimmer 6 | 118 | 10.3.118.0/24 |
| Zimmer 7 | 119 | 10.3.119.0/24 |

## Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Production Deployment

### 1. Build

```bash
docker-compose build
```

### 2. Init DB

```bash
docker-compose run --rm backend python -m app.init_data
```

### 3. Start

```bash
docker-compose up -d
```

### 4. Logs

```bash
docker-compose logs -f
docker-compose logs backend
docker-compose logs frontend
```

### 5. Stop

```bash
docker-compose down
```

## Firewall (nftables)

### Manual Commands

```bash
# Block VLAN 18
nft add rule inet filter forward ip saddr 10.3.18.0/24 drop

# List rules with handles
nft -a list chain inet filter forward

# Delete rule by handle
nft delete rule inet filter forward handle <handle>

# Flush all forward rules
nft flush chain inet filter forward
```

### Check Status

```bash
# Via API
curl http://localhost:8000/api/rooms

# Via nftables
nft list chain inet filter forward | grep drop
```

## API Endpoints

### Authentication
- `POST /api/login` - Login (returns JWT token)

### Rooms (All 7 visible to everyone)
- `GET /api/rooms` - Get ALL rooms
- `POST /api/rooms/{id}/toggle?enable=true|false` - Toggle internet

### Whitelists (per room)
- `GET /api/whitelists?room_id=1` - Get whitelists (optionally filtered by room)
- `POST /api/whitelists` - Create whitelist (requires room_id)
- `DELETE /api/whitelists/{id}` - Delete whitelist

### Health Check
- `GET /api/health` - Service status

## Tech Stack

**Frontend:**
- Vue 3 (Composition API)
- TypeScript
- Vite (Build tool)
- Axios (HTTP client)
- CSS3 (Custom styling with gradients)

**Backend:**
- FastAPI (Python 3.11)
- SQLAlchemy (ORM)
- JWT Authentication (python-jose)
- bcrypt (Password hashing)
- nftables (Firewall control)

**Infrastructure:**
- Docker + Docker Compose
- Nginx (Reverse proxy + Static serving)
- SQLite (Database)

## Screenshots

### Login
- Simple username/password form
- Test credentials provided

### Dashboard
- Grid view of all 7 rooms
- Status indicator (🟢 Active / 🔴 Blocked)
- Toggle button per room
- Click room to manage whitelists

### Whitelist Management
- Select a room
- Create/view/delete whitelists
- URL list per template
- Easy copy from templates

## Roadmap

### Phase 1: MVP (Current)
- ✅ Multi-room dashboard
- ✅ Internet EIN/AUS
- ✅ Whitelist management
- ✅ Basic auth

### Phase 2: LDAP Integration
- 🔜 Active Directory authentication
- 🔜 Auto-login via AD groups
- 🔜 No local user management

### Phase 3: Advanced Features
- ⏳ Schedule-based blocking
- ⏳ Activity logs
- ⏳ Email notifications
- ⏳ Mobile app

## Troubleshooting

### Frontend not loading
```bash
docker-compose logs frontend
# Check if Nginx is running
curl http://localhost:8080
```

### Backend errors
```bash
docker-compose logs backend
# Check if FastAPI is running
curl http://localhost:8000/api/health
```

### nftables not working
```bash
# Check if container has host network access
docker inspect internet-control-backend | grep NetworkMode
# Should be "host"

# Check nftables on host
nft list ruleset
```

### Database issues
```bash
# Recreate database
rm -f data/internet_control.db
docker-compose run --rm backend python -m app.init_data
```

## License

MIT License - Hackathon 2026

## Team

**RaphiClaw** 🦇  
Built at zB. Zentrum Bildung Baden Hackathon

## Links

- [GitHub Repository](https://github.com/raphiclaw/internet-ein-aus)
- [Architecture Visualization](./architecture.html)
- [Challenge Description](./REQUIREMENTS_FINAL.md)
