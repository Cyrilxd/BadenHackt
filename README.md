# Internet EIN/AUS - Hackathon Challenge 1

Web-basiertes Kontrollpanel für Lehrer zur Steuerung des Internetzugangs in 7 Schulräumen (VLANs) am zB. Zentrum Bildung Baden.

## 🎯 Features

- ✅ **Multi-Room Control**: Alle Lehrer können alle 7 Räume steuern
- ✅ **Internet Toggle**: Internet pro Raum aktivieren/deaktivieren
- ✅ **URL-Whitelist**: Pro-Raum Whitelist-Verwaltung
- ✅ **Modern Stack**: Vue 3 + TypeScript Frontend, FastAPI Backend
- ✅ **Docker Deployment**: Vollständig containerisiert
- ✅ **Firewall Integration**: Remote Firewall-Agent für Shorewall/MOCK

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
│  Auth: JWT / LDAP                                   │
└────────────────┬────────────────────────────────────┘
                 │
                 │ HTTP room policy sync
                 │
┌────────────────▼────────────────────────────────────┐
│  Firewall Agent (FastAPI)                           │
│  Port: 8081 (mock in Compose)                       │
│  Driver: mock | shorewall                           │
└────────────────┬────────────────────────────────────┘
                 │
                 │ local command execution on firewall host
                 │
┌────────────────▼────────────────────────────────────┐
│  Shorewall Firewall Host                            │
│  Managed rules per VLAN and room whitelist          │
│  7 VLANs: 18-22, 118-119                            │
└─────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Voraussetzungen

- **Docker** & **Docker Compose** installiert
- Für den Mock: keine Firewall-Hardware nötig
- Für Produktion: ein erreichbarer Debian/Shorewall-Host für den Firewall-Agent

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
**Firewall Mock API**: http://localhost:8081  
**API Dokumentation**: http://localhost:8000/docs

### 4. Login

**Test-Accounts** (vor LDAP-Integration):

| Username | Password | Rolle   |
|----------|----------|---------|
| lehrer   | admin123 | Teacher |
| mueller  | admin123 | Teacher |
| schmidt  | admin123 | Teacher |

Mit der Compose-Umgebung läuft jetzt zusätzlich ein OpenLDAP-Testverzeichnis auf `ldap://localhost:389`. Das Backend verwendet standardmässig `AUTH_MODE=ldap` und authentifiziert die gleichen Test-Accounts gegen LDAP.

### LDAP Test Directory

- Base DN: `dc=hackathon,dc=local`
- Bind DN: `cn=admin,dc=hackathon,dc=local`
- Bind Password: `admin`
- User Search Base: `ou=users,dc=hackathon,dc=local`
- Test Group: `cn=teachers,ou=groups,dc=hackathon,dc=local`

Die LDIF-Seed-Daten liegen in [docker/openldap/ldif/10-users-and-groups.ldif](/Users/daniel/dev/BadenHackt/docker/openldap/ldif/10-users-and-groups.ldif).

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
│   │   ├── firewall.py     # Remote firewall agent client
│   │   ├── database.py     # SQLAlchemy Models
│   │   └── init_data.py    # Test-Daten Generator
│   ├── Dockerfile
│   └── requirements.txt
├── firewall-agent/         # Firewall API für Mock/Shorewall
│   ├── app/main.py         # Room policy sync + Shorewall driver
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

Wichtige Backend-Variablen:

```env
SECRET_KEY=your-secret-key-here-change-in-production
DATABASE_URL=sqlite:///./internet_control.db
FIREWALL_API_URL=http://shorewall-mock:8080
FIREWALL_API_TOKEN=change-me
```

Wichtige Firewall-Agent-Variablen auf dem echten Firewall-Host:

```env
FIREWALL_DRIVER=shorewall
FIREWALL_API_TOKEN=change-me
SHOREWALL_SOURCE_ZONE=loc
SHOREWALL_DEST_ZONE=net
SHOREWALL_RULES_FILE=/etc/shorewall/rules
SHOREWALL_MANAGED_RULES_FILE=/etc/shorewall/rules.d/badenhackt.rules
```

### Firewall-Verhalten

- Der Backend-Server synchronisiert pro Zimmer immer die komplette Policy: `internet_enabled` plus die aggregierte Whitelist aller gespeicherten Listen dieses Zimmers.
- In der Compose-Umgebung läuft der Agent im `mock`-Modus und schreibt die gerenderten Regeln nach [`data/firewall-agent/mock/badenhackt.rules`](/Users/daniel/dev/BadenHackt/data/firewall-agent/mock/badenhackt.rules).
- Auf dem echten Firewall-Host läuft derselbe Agent mit `FIREWALL_DRIVER=shorewall` und erzeugt ein Shorewall-Include-File sowie die passenden `ipset`-Einträge.
- Whitelist-Einträge werden vor dem Speichern auf Hostnamen normalisiert. `https://google.com/path` wird z.B. zu `google.com`.
- Wildcard-Präfixe wie `*.example.org` werden auf `example.org` reduziert, weil die Shorewall-Synchronisation mit aufgelösten IP-Zielen arbeitet.

## 🔐 Sicherheit

### LDAP-Integration (TODO)

Für Produktion kann die Test-Konfiguration durch das echte Verzeichnis ersetzt werden:

**Benötigte Informationen:**
- LDAP Server Hostname/IP
- Port (389 oder 636 für LDAPS)
- Base DN
- Bind-Methode (Simple Bind oder Service Account)

**Integration:**
1. `AUTH_MODE=ldap` oder `AUTH_MODE=auto` setzen
2. `LDAP_HOST`, `LDAP_PORT`, `LDAP_BASE_DN`, `LDAP_BIND_DN`, `LDAP_BIND_PASSWORD` anpassen
3. Falls nötig `LDAP_USER_SEARCH_BASE` und `LDAP_USER_SEARCH_FILTER` für Active Directory ändern

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
# Mock-Regeln prüfen
sed -n '1,120p' data/firewall-agent/mock/badenhackt.rules

# Agent-Logs prüfen
docker-compose logs shorewall-mock
```

Wenn der Agent auf dem echten Firewall-Host läuft:

```bash
shorewall check
shorewall refresh
ipset list
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
- `POST /api/whitelists` - URL/Domain zur Whitelist hinzufügen und auf Firewall synchronisieren
- `PUT /api/whitelists/{id}` - Whitelist aktualisieren und auf Firewall synchronisieren
- `DELETE /api/whitelists/{whitelist_id}` - URL von Whitelist entfernen

## 📄 Lizenz

MIT License - siehe LICENSE Datei

## 👥 Team

Entwickelt für den zB. Zentrum Bildung Baden Hackathon.

---

**Status**: ✅ MVP Ready | 🚧 LDAP Integration pending
