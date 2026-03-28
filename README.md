# OnOffLine

Web-basiertes Kontrollpanel für Lehrpersonen zur Steuerung des Internetzugangs in 7 Schulzimmern. Pro Raum kann der Internetzugang ein- oder ausgeschaltet sowie eine Whitelist gepflegt werden.

Die technische Detailarchitektur ist in [`ARCHITECTURE.md`](./ARCHITECTURE_revised.md) dokumentiert.

## Ziel des Projekts

Die Anwendung ermöglicht es, den Internetzugang pro Schulzimmer einfach und zentral zu steuern, ohne direkt auf der Firewall arbeiten zu müssen.

## Funktionsumfang

- Multi-Room-Steuerung für 7 Schulzimmer
- Internet pro Raum aktivieren oder deaktivieren
- URL-Whitelist pro Raum verwalten
- Web-Frontend mit Vue 3 und TypeScript
- Backend mit FastAPI
- Containerisiertes Deployment mit Docker Compose
- Anbindung an einen Firewall-Agent für Mock oder Shorewall
- LDAP-Testverzeichnis in der Compose-Umgebung

## Systemüberblick

Die Anwendung besteht aus vier Hauptkomponenten:

- **Frontend** für Login und Bedienung
- **Backend** für Authentifizierung, Raumlogik und Persistenz
- **Firewall-Agent** für die Synchronisation der Raum-Policies auf die Firewall
- **SQLite** für Benutzer-, Raum- und Whitelist-Daten

Eine technische Darstellung mit Datenflüssen, Komponenten und Verantwortlichkeiten befindet sich in `ARCHITECTURE.md`.

## Quick Start

### Voraussetzungen

- Docker
- Docker Compose

Für den Mock-Betrieb ist keine echte Firewall-Hardware nötig. Für einen produktiven Betrieb wird ein erreichbarer Shorewall-Host für den Firewall-Agent benötigt.

### Repository klonen

```bash
git clone https://github.com/Cyrilxd/BadenHackt.git
cd BadenHackt
```

### Container starten

```bash
docker-compose up -d
```

Optionale Logs:

```bash
docker-compose logs -f
```

## Zugriff auf die Anwendung

- **Frontend:** `http://localhost`
- **Backend API:** `http://localhost:8000`
- **API-Dokumentation:** `http://localhost:8000/docs`
- **Firewall Mock API:** `http://localhost:8081`

## Login und Testdaten

### Test-Accounts

| Username | Password | Rolle |
|----------|----------|-------|
| lehrer   | admin123 | Teacher |
| mueller  | admin123 | Teacher |
| schmidt  | admin123 | Teacher |

### LDAP-Testverzeichnis

In der Compose-Umgebung läuft zusätzlich ein OpenLDAP-Testverzeichnis.

- **LDAP URL:** `ldap://localhost:389`
- **Base DN:** `dc=hackathon,dc=local`
- **Bind DN:** `cn=admin,dc=hackathon,dc=local`
- **Bind Password:** `admin`
- **User Search Base:** `ou=users,dc=hackathon,dc=local`
- **Test Group:** `cn=teachers,ou=groups,dc=hackathon,dc=local`

Das Backend verwendet standardmässig `AUTH_MODE=ldap` und authentifiziert die Test-Accounts gegen dieses Verzeichnis.

## Schulzimmer und VLANs

| Raum     | VLAN ID | Subnet        |
|----------|---------|---------------|
| Zimmer 1 | 18      | 10.3.18.0/24  |
| Zimmer 2 | 19      | 10.3.19.0/24  |
| Zimmer 3 | 20      | 10.3.20.0/24  |
| Zimmer 4 | 21      | 10.3.21.0/24  |
| Zimmer 5 | 22      | 10.3.22.0/24  |
| Zimmer 6 | 118     | 10.3.118.0/24 |
| Zimmer 7 | 119     | 10.3.119.0/24 |

## Projektstruktur

```text
internet-ein-aus/
├── backend/               # FastAPI Backend
├── firewall-agent/        # Agent für Mock oder Shorewall
├── frontend/              # Vue 3 Frontend
├── docker-compose.yml     # Lokale Orchestrierung
├── README.md              # Einstieg, Setup, Betrieb
└── ARCHITECTURE.md        # Technische Detailarchitektur
```

## Lokale Entwicklung

### Backend lokal starten

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend lokal starten

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

## Konfiguration

### Relevante Backend-Variablen

```env
SECRET_KEY=your-secret-key-here-change-in-production
DATABASE_URL=sqlite:///./internet_control.db
FIREWALL_API_URL=http://shorewall-mock:8080
FIREWALL_API_TOKEN=change-me
```

### Relevante Firewall-Agent-Variablen

```env
FIREWALL_DRIVER=shorewall
FIREWALL_API_TOKEN=change-me
SHOREWALL_SOURCE_ZONE=loc
SHOREWALL_DEST_ZONE=net
SHOREWALL_RULES_FILE=/etc/shorewall/rules
SHOREWALL_MANAGED_RULES_FILE=/etc/shorewall/rules.d/badenhackt.rules
```

## Verhalten der Firewall-Synchronisation

- Das Backend synchronisiert pro Raum immer die komplette Policy.
- Diese Policy besteht aus `internet_enabled` und der aggregierten Whitelist des jeweiligen Raums.
- In der Compose-Umgebung läuft der Agent im `mock`-Modus.
- Auf einem echten Firewall-Host läuft derselbe Agent mit `FIREWALL_DRIVER=shorewall`.
- Whitelist-Einträge werden vor dem Speichern auf Hostnamen normalisiert.
- Wildcard-Präfixe wie `*.example.org` werden auf `example.org` reduziert.

## API-Endpunkte

### Authentication

- `POST /api/login`

### Rooms

- `GET /api/rooms`
- `POST /api/rooms/{room_id}/toggle`

### Whitelist

- `GET /api/whitelists?room_id={id}`
- `POST /api/whitelists`
- `PUT /api/whitelists/{id}`
- `DELETE /api/whitelists/{whitelist_id}`

## Sicherheit

### LDAP für Produktion

Für Produktion kann die Test-Konfiguration durch ein echtes LDAP-Verzeichnis ersetzt werden.

Dafür werden mindestens folgende Angaben benötigt:

- LDAP Hostname oder IP
- LDAP Port
- Base DN
- Bind-Methode
- Optional angepasste Search Base und Search Filter

## Troubleshooting

### Container starten nicht

```bash
docker-compose logs
docker-compose down
docker-compose up --build -d
```

### Firewall-Regeln prüfen

```bash
sed -n '1,120p' data/firewall-agent/mock/badenhackt.rules
docker-compose logs shorewall-mock
```

Auf einem echten Firewall-Host zusätzlich:

```bash
shorewall check
shorewall refresh
ipset list
```

### Frontend erreicht Backend nicht

```bash
curl http://localhost:8000/docs
docker-compose ps
```

## Lizenz

MIT License

## Team

- Raphael Bapst: https://www.linkedin.com/in/raphael-bapst/
- Michael Bapst: https://www.linkedin.com/in/michael-bapst-480368255/
- Daniel Butler: https://www.linkedin.com/in/danielbutlerismyname/
- Cyril Heiniger: https://www.linkedin.com/in/cyril-heiniger/

Entwickelt für das zB. Zentrum Bildung Baden  am BadenHackt Hackathon.
