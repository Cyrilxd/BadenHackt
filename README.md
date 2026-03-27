# Internet EIN/AUS - Schulzimmer-Kontrolle

Hackathon Challenge für zB. Zentrum Bildung Baden

## Features

- ✅ Internet EIN/AUS pro Schulzimmer (7 VLANs)
- ✅ URL-Whitelist-Management
- ✅ 1 Admin-User pro Zimmer
- ✅ Vue 3 + TypeScript Frontend
- ✅ FastAPI Backend
- ✅ nftables Firewall-Integration
- ✅ Docker Compose Deployment

## Architektur

```
Internet → Firewall → Perimeter Firewall (Docker) → 7 VLANs
                     ├── Frontend (Nginx + Vue)
                     ├── Backend (FastAPI)
                     └── nftables (Host)
```

## Setup

### 1. Init Database

```bash
cd backend
python -m app.init_data
```

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Access

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000/docs

## Test-Logins

| Username | Password | Zimmer | VLAN |
|----------|----------|--------|------|
| vlan18   | admin123 | Zimmer 1 | 10.3.18.0/24 |
| vlan19   | admin123 | Zimmer 2 | 10.3.19.0/24 |
| vlan20   | admin123 | Zimmer 3 | 10.3.20.0/24 |
| vlan21   | admin123 | Zimmer 4 | 10.3.21.0/24 |
| vlan22   | admin123 | Zimmer 5 | 10.3.22.0/24 |
| vlan118  | admin123 | Zimmer 6 | 10.3.118.0/24 |
| vlan119  | admin123 | Zimmer 7 | 10.3.119.0/24 |

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
docker-compose run backend python -m app.init_data
```

### 3. Start

```bash
docker-compose up -d
```

### 4. Logs

```bash
docker-compose logs -f
```

## Firewall Commands

### Manual nftables

```bash
# Block VLAN 18
nft add rule inet filter forward ip saddr 10.3.18.0/24 drop

# List rules
nft -a list chain inet filter forward

# Delete rule by handle
nft delete rule inet filter forward handle <handle>
```

## API Endpoints

### Auth
- `POST /api/login` - Login (returns JWT)

### Rooms
- `GET /api/rooms` - Get user's room
- `POST /api/rooms/{id}/toggle` - Toggle internet (enable=true/false)

### Whitelists
- `GET /api/whitelists` - List whitelists
- `POST /api/whitelists` - Create whitelist
- `DELETE /api/whitelists/{id}` - Delete whitelist

## Tech Stack

**Frontend:**
- Vue 3 + TypeScript
- Vite
- Axios
- CSS3 (Gradients)

**Backend:**
- FastAPI
- SQLAlchemy
- JWT (python-jose)
- bcrypt
- nftables

**Infrastructure:**
- Docker + Docker Compose
- Nginx
- SQLite

## License

MIT License - Hackathon 2026

## Team

RaphiClaw 🦇

## Screenshots

(Siehe `architecture.html` für visuelle Architektur)
