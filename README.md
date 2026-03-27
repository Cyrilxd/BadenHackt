# Internet EIN/AUS - Hackathon Challenge 1

Web-basiertes Kontrollpanel für Lehrer zur Steuerung des Internetzugangs in 7 Schulräumen (VLANs) am zB. Zentrum Bildung Baden.

## 🎯 Features

- ✅ **Multi-Room Control**: Alle Lehrer können alle 7 Räume steuern
- ✅ **Internet Toggle**: Internet pro Raum aktivieren/deaktivieren
- ✅ **URL-Whitelist**: Pro-Raum Whitelist-Verwaltung
- ✅ **Modern Stack**: Vue 3 + TypeScript Frontend, FastAPI Backend
- ✅ **Docker Deployment**: Vollständig containerisiert
- ✅ **Firewall Integration**: nftables für Netzwerk-Kontrolle

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────┐
│  Frontend (Vue 3 + TypeScript)                      │
│  Port: 80 (nginx)                                   │
└────────────────┬────────────────────────────────────┘
                 │
                 │ HTTP/REST
                 │
┌────────────────▼────────────────────────────────────┐
│  Backend (FastAPI + SQLAlchemy)                     │
│  Port: 8000                                         │
│  Auth: JWT (später LDAP)                            │
└────────────────┬────────────────────────────────────┘
                 │
                 │ nftables commands
                 │
┌────────────────▼────────────────────────────────────┐
│  Host Firewall (nftables)                           │
│  7 VLANs: 18-22, 118-119                           │
│  Subnets: 10.3.x.0/24                               │
└─────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Voraussetzungen

- **Docker** & **Docker Compose** installiert
- **nftables** auf dem Host installiert
- **Root/Sudo-Rechte** für Firewall-Operationen

### 1. Repository klonen

```bash
git clone https://github.com/raphiclaw/internet-ein-aus.git
cd internet-ein-aus
```

### 2. Anwendung starten

```bash
# Container bauen und starten
docker-compose up -d

# Logs anzeigen (optional)
docker-compose logs -f
```

### 3. Zugriff auf die Anwendung

**Frontend**: http://localhost (Port 80)  
**Backend API**: http://localhost:8000  
**API Dokumentation**: http://localhost:8000/docs

### 4. Login

**Test-Accounts** (vor LDAP-Integration):

| Username | Password | Rolle   |
|----------|----------|---------|
| lehrer   | admin123 | Teacher |
| mueller  | admin123 | Teacher |
| schmidt  | admin123 | Teacher |

## 🏫 Räume & VLANs

| Raum     | VLAN ID | Subnet         |
|----------|---------|----------------|
| Zimmer 1 | 18      | 10.3.18.0/24   |
| Zimmer 2 | 19      | 10.3.19.0/24   |
| Zimmer 3 | 20      | 10.3.20.0/24   |
| Zimmer 4 | 21      | 10.3.21.0/24   |
| Zimmer 5 | 22      | 10.3.22.0/24   |
| Zimmer 6 | 118     | 10.3.118.0/24  |
| Zimmer 7 | 119     | 10.3.119.0/24  |

## 📦 Projekt-Struktur

```
internet-ein-aus/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── main.py         # API Endpoints
│   │   ├── auth.py         # JWT Authentication
│   │   ├── firewall.py     # nftables Integration
│   │   ├── database.py     # SQLAlchemy Models
│   │   └── init_data.py    # Test-Daten Generator
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Vue 3 Frontend
│   ├── src/
│   │   ├── App.vue
│   │   ├── components/
│   │   │   ├── Login.vue
│   │   │   └── Dashboard.vue
│   │   └── api.ts         # API Client
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml      # Container Orchestrierung
└── README.md
```

## 🔧 Entwicklung

### Backend starten (lokal)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend starten (lokal)

```bash
cd frontend
npm install
npm run dev
```

### Testdaten initialisieren

```bash
cd backend
python -m app.init_data
```

## 🛠️ Konfiguration

### Umgebungsvariablen (Backend)

Erstelle `.env` im `backend/` Ordner:

```env
SECRET_KEY=your-secret-key-here-change-in-production
DATABASE_URL=sqlite:///./internet_control.db
```

### Docker Compose Anpassungen

**Wichtig**: Der Backend-Container benötigt `privileged: true` und `network_mode: host` für nftables-Zugriff:

```yaml
backend:
  privileged: true
  network_mode: host
```

## 🔐 Sicherheit

### LDAP-Integration (TODO)

Für Produktion muss LDAP gegen Active Directory integriert werden:

**Benötigte Informationen:**
- LDAP Server Hostname/IP
- Port (389 oder 636 für LDAPS)
- Base DN
- Bind-Methode (Simple Bind oder Service Account)

**Integration:**
1. `python-ldap` oder `ldap3` zu `requirements.txt` hinzufügen
2. `auth.py` anpassen für LDAP-Authentifizierung
3. Test-User durch LDAP-Abfrage ersetzen

## 🐛 Troubleshooting

### Container starten nicht

```bash
# Logs prüfen
docker-compose logs

# Container neu bauen
docker-compose down
docker-compose up --build -d
```

### Firewall-Regeln funktionieren nicht

```bash
# nftables Status prüfen
sudo nft list ruleset

# Backend-Container muss privilegiert sein
# Prüfe docker-compose.yml: privileged: true
```

### Frontend kann Backend nicht erreichen

```bash
# Backend-Status prüfen
curl http://localhost:8000/docs

# Netzwerk-Konfiguration prüfen
docker-compose ps
```

## 📝 API Endpoints

### Authentication
- `POST /api/login` - Login (form-data: username, password)

### Rooms
- `GET /api/rooms` - Alle Räume abrufen
- `POST /api/rooms/{room_id}/toggle` - Internet aktivieren/deaktivieren

### Whitelist
- `GET /api/whitelists?room_id={id}` - Whitelist eines Raums abrufen
- `POST /api/whitelists` - URL zur Whitelist hinzufügen
- `DELETE /api/whitelists/{whitelist_id}` - URL von Whitelist entfernen

## 📄 Lizenz

MIT License - siehe LICENSE Datei

## 👥 Team

Entwickelt für den zB. Zentrum Bildung Baden Hackathon.

---

**Status**: ✅ MVP Ready | 🚧 LDAP Integration pending
