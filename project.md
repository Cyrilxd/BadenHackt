# Internet EIN/AUS - Schulzimmer-Kontrolle

## Projektübersicht

Hackathon-Projekt für zB. Zentrum Bildung Baden. Webbasierte Steuerung des Internetzugangs in 7 Schulzimmern (VLANs). Jeder angemeldete Lehrer kann alle Zimmer steuern und URL-Whitelists pro Zimmer verwalten.

## Status

- MVP: In Entwicklung
- Version: 2.0.0

## Tech Stack

| Komponente | Technologie |
|------------|------------|
| Frontend   | Vue 3 + TypeScript + Vite |
| Backend    | FastAPI (Python 3.11) |
| Datenbank  | SQLite |
| Auth       | JWT (python-jose) + bcrypt |
| Firewall   | nftables |
| Deployment | Docker Compose |
| Webserver  | Nginx (Reverse Proxy + Static) |

## Architektur

```
Internet → Firewall → Perimeter Firewall (Docker) → 7 VLANs
                     ├── Frontend (Nginx + Vue 3 + TypeScript) :8080
                     ├── Backend (FastAPI + nftables)          :8000
                     └── SQLite (Users + Rooms + Whitelists)
```

## Datenbank-Schema

### users
| Spalte        | Typ     | Beschreibung                 |
|---------------|---------|------------------------------|
| id            | INTEGER | Primary Key, Auto-Increment  |
| username      | TEXT    | Eindeutig, Index             |
| password_hash | TEXT    | bcrypt-Hash                  |
| vlan_id       | INTEGER | 0 = Zugriff auf alle Räume   |
| room_name     | TEXT    | Anzeigename                  |

### rooms
| Spalte           | Typ     | Beschreibung               |
|------------------|---------|----------------------------|
| id               | INTEGER | Primary Key, Auto-Increment|
| name             | TEXT    | z.B. "Zimmer 1"            |
| subnet           | TEXT    | z.B. "10.3.18.0/24"        |
| vlan_id          | INTEGER | Eindeutig, z.B. 18         |
| internet_enabled | BOOLEAN | Default: True              |

### whitelist_templates
| Spalte  | Typ     | Beschreibung                    |
|---------|---------|----------------------------------|
| id      | INTEGER | Primary Key, Auto-Increment      |
| name    | TEXT    | z.B. "Google Suite"              |
| urls    | TEXT    | JSON-Array als String            |
| room_id | INTEGER | FK → rooms.id                    |

## VLANs / Schulzimmer

| Zimmer   | VLAN | Subnetz          |
|----------|------|------------------|
| Zimmer 1 | 18   | 10.3.18.0/24     |
| Zimmer 2 | 19   | 10.3.19.0/24     |
| Zimmer 3 | 20   | 10.3.20.0/24     |
| Zimmer 4 | 21   | 10.3.21.0/24     |
| Zimmer 5 | 22   | 10.3.22.0/24     |
| Zimmer 6 | 118  | 10.3.118.0/24    |
| Zimmer 7 | 119  | 10.3.119.0/24    |

## API-Endpunkte

| Methode | Pfad                      | Beschreibung              | Auth |
|---------|---------------------------|---------------------------|------|
| POST    | /api/login                | Login, JWT-Token zurück   | Nein |
| GET     | /api/rooms                | Alle 7 Zimmer abrufen     | JWT  |
| POST    | /api/rooms/{id}/toggle    | Internet EIN/AUS          | JWT  |
| GET     | /api/whitelists           | Whitelists (opt. room_id) | JWT  |
| POST    | /api/whitelists           | Whitelist erstellen        | JWT  |
| DELETE  | /api/whitelists/{id}      | Whitelist löschen          | JWT  |
| GET     | /api/health               | Health Check               | Nein |

## Test-Benutzer

| Username | Passwort | Beschreibung  |
|----------|----------|---------------|
| lehrer   | admin123 | Test Lehrer   |
| mueller  | admin123 | Herr Müller   |
| schmidt  | admin123 | Frau Schmidt  |

Alle Benutzer können **alle 7 Zimmer** steuern.

## Projektstruktur

```
BadenHackt/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI App + Routen
│   │   ├── auth.py          # JWT Auth + Passwort-Hashing
│   │   ├── database.py      # SQLAlchemy Models + DB-Setup
│   │   ├── firewall.py      # nftables Management
│   │   ├── schemas.py       # Pydantic-Modelle (inkl. Whitelist-URLs)
│   │   ├── validators.py    # Whitelist-Host-Extraktion + Validierung
│   │   └── init_data.py     # Testdaten-Initialisierung
│   ├── tests/               # pytest (dev: requirements-dev.txt)
│   ├── schema.sql           # DB-Schema (Referenz)
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.vue  # Zimmer-Grid + Whitelist-Mgmt
│   │   │   └── Login.vue      # Login-Formular
│   │   ├── tailwind-plus/
│   │   │   └── vue/           # Tailwind Plus (Vue) UI-Blöcke (Referenz, 657 Dateien)
│   │   ├── api.ts             # Axios API-Client
│   │   ├── App.vue            # Root-Komponente + Auth-State
│   │   ├── main.ts            # Vue App Bootstrap
│   │   └── style.css          # Globale Styles
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── architecture.html          # Interaktive Architektur-Visualisierung
└── project.md                 # Diese Datei
```

## Umgebungsvariablen

| Variable   | Beschreibung         | Default                              |
|------------|---------------------|--------------------------------------|
| SECRET_KEY | JWT Signing Key     | hackathon-2026-change-in-production  |
| VITE_API_URL | Backend URL (Dev) | http://localhost:8000                |

## Changelog

### 2026-03-27 - Whitelist-Host-Validierung (Backend)
- `backend/app/validators.py`: Extraktion wie bisher, plus syntaktische Prüfung (IPv4/IPv6 über `ipaddress`, Domainnamen über IDNA + RFC-1035-Labels, Längenlimits als Konstanten).
- `backend/app/schemas.py`: `WhitelistCreate` / `WhitelistUpdate` nutzen `parse_whitelist_url_entry`; ungültige Einträge liefern klare Fehlermeldungen (422).
- Tests: `backend/tests/test_url_validation.py`, Ausführung mit `pip install -r requirements-dev.txt` und `pytest` im Ordner `backend/`.

### 2026-03-27 - Tailwind Plus Vue (lokale Komponenten)
- `frontend/src/tailwind-plus/vue/`: vollständiger Inhalt von `tailwind-plus-components/components/vue` (UI-Blocks als `.vue`-Dateien). Nutzung setzt passendes Tailwind-CSS-Setup voraus; App-Views (`Login`/`Dashboard`) sind davon unverändert.

### 2026-03-27 - Projekt-Bereinigung
- Backend: `__init__.py` erstellt (fehlte)
- Backend: `firewall.py` Bug in `get_vlan_status()` behoben (Zeilen-Check)
- Backend: `database.py` auf SQLAlchemy 2.0 `DeclarativeBase` migriert
- Backend: `main.py` auf FastAPI Lifespan migriert (statt deprecated `on_event`)
- Backend: `auth.py` SECRET_KEY aus Environment, `utcnow()` → `now(timezone.utc)`
- Backend: `schema.sql` an SQLAlchemy-Models angeglichen
- Frontend: `HelloWorld.vue` entfernt (unbenutzte Template-Datei)
- Frontend: `style.css` aufgeräumt (Template-Styles entfernt)
- Frontend: `index.html` Titel + Sprache korrigiert
- Frontend: `vite.config.ts` Dev-Proxy für `/api` hinzugefügt
- Frontend: `Login.vue` Input box-sizing gefixt
- Frontend: `Dashboard.vue` Prop-Typ an App.vue angeglichen
- Docker: `network_mode: host` entfernt (Konflikt mit Ports)
- Docker: Nginx proxy_pass auf Container-Name geändert
- Docker: Unbenutzte Volume entfernt
- Doku: `project.md` erstellt
- Doku: `REQUIREMENTS_FINAL.md` und `SETUP_STATUS.md` aktualisiert
