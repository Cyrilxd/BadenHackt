# Hackathon Infrastructure - READY ✅

## Installierte Tools

### Networking & Firewall
- ✅ **nftables** 1.1.6
- ✅ **squid** 7.5 (Proxy + URL filtering)
- ✅ **dnsmasq** 2.92 (DNS)
- ✅ **nginx** 1.29.7 (Web server)

### Development
- ✅ **Python** 3.11 (venv im backend/)
- ✅ **Node.js** 25.8.2
- ✅ **SQLite** 3.51.3

### Network Tools
- ✅ tcpdump, netcat, bind (DNS utils)

---

## Projekt-Struktur

```
BadenHackt/
├── backend/
│   ├── app/               ✅ FastAPI App (main, auth, database, firewall)
│   ├── requirements.txt   ✅ FastAPI, SQLAlchemy, etc.
│   ├── schema.sql         ✅ DB-Schema (Referenz)
│   └── Dockerfile         ✅ Python 3.11-slim
├── frontend/
│   ├── src/               ✅ Vue 3 + TypeScript (App, Dashboard, Login)
│   ├── package.json       ✅ Vite, Vue, Axios
│   ├── nginx.conf         ✅ Reverse Proxy Config
│   └── Dockerfile         ✅ Multi-stage Build
├── docker-compose.yml     ✅ Backend + Frontend
├── data/                  📁 SQLite DB (Volume)
└── project.md             ✅ Projektdokumentation
```

---

## Backend Dependencies (Python venv)
- fastapi 0.109.0
- uvicorn 0.27.0
- sqlalchemy 2.0.25
- aiosqlite 0.19.0
- bcrypt 4.1.2
- python-jose (JWT auth)

## Frontend Dependencies (npm)
- vite 8.x (build tool)
- vue 3.5.x (UI framework)
- vue-tsc (TypeScript compiler)
- axios (HTTP client)

---

## Datenbank Schema

**Tables:**
- `users` - Lehrer-Logins (username, password_hash, vlan_id, room_name)
- `rooms` - Schulzimmer (name, subnet, vlan_id, internet_enabled)
- `whitelist_templates` - URL-Listen pro Zimmer (name, urls, room_id)

---

## Nächste Schritte (morgen)

1. **Netzwerk-Details klären** (Gateway-Setup, DNS-Routing)
2. **Backend API entwickeln** (FastAPI endpoints)
3. **Frontend GUI bauen** (React SPA)
4. **nftables Rules implementieren** (Internet sperren/freigeben)
5. **Squid Whitelist-Integration**
6. **Zeitplan-Automation** (Cron/Scheduler)

---

**Status:** Alle Tools installiert, Projekt-Struktur steht, DB initialisiert. Ready für Hackathon! 🦇
