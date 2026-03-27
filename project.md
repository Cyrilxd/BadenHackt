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
| Spalte    | Typ     | Beschreibung                    |
|-----------|---------|----------------------------------|
| id        | INTEGER | Primary Key, Auto-Increment      |
| name      | TEXT    | z.B. "Google Suite"              |
| urls      | TEXT    | JSON-Array als String            |
| room_id   | INTEGER | FK → rooms.id                    |
| is_active | BOOLEAN | Whitelist aktiv (Default: True)  |

### audit_logs
| Spalte    | Typ      | Beschreibung                                   |
|-----------|----------|------------------------------------------------|
| id        | INTEGER  | Primary Key, Auto-Increment                    |
| timestamp | DATETIME | UTC, Index                                     |
| username  | TEXT     | Handelnder Benutzer, Index                     |
| action    | TEXT     | Aktionstyp (z. B. internet_toggle), Index      |
| target    | TEXT     | Zielobjekt (z. B. "Zimmer 1 (VLAN 18)"), opt. |
| detail    | TEXT     | JSON-String mit Zusatzinfos, optional          |
| success   | BOOLEAN  | True = erfolgreich, False = gescheitert        |

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
| POST    | /api/login                | Login, JWT-Token zurück           | Nein |
| GET     | /api/rooms                | Alle 7 Zimmer abrufen             | JWT  |
| POST    | /api/rooms/{id}/toggle    | Internet EIN/AUS                  | JWT  |
| GET     | /api/whitelists           | Whitelists (opt. room_id)         | JWT  |
| POST    | /api/whitelists           | Whitelist erstellen               | JWT  |
| PUT     | /api/whitelists/{id}      | Whitelist aktualisieren           | JWT  |
| PATCH   | /api/whitelists/{id}/toggle | Whitelist aktivieren/deaktivieren | JWT  |
| DELETE  | /api/whitelists/{id}      | Whitelist löschen                 | JWT  |
| GET     | /api/audit                | Audit-Log (filter: user/action/success/limit) | JWT  |
| GET     | /api/health               | Health Check                      | Nein |

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
│   │   ├── audit.py         # AuditAction Enum + log_action()
│   │   └── init_data.py     # Testdaten-Initialisierung
│   ├── tests/               # pytest (dev: requirements-dev.txt)
│   ├── schema.sql           # DB-Schema (Referenz)
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── dashboard/     # RoomCard, PageTitle, WhitelistModal, AuditLog
│   │   │   ├── layout/        # AppTopBar
│   │   │   ├── ui/            # UiButton, UiModal (wiederverwendbar)
│   │   │   ├── Dashboard.vue  # Orchestrierung Zimmer + Modal
│   │   │   └── Login.vue
│   │   ├── constants/
│   │   │   └── copy.ts        # Deutsche UI-Texte (eine Quelle)
│   │   ├── styles/
│   │   │   ├── tokens.css     # Design-Tokens (Farben, Radii, Layout)
│   │   │   └── base.css       # Reset + body (importiert tokens)
│   │   ├── api.ts
│   │   ├── App.vue
│   │   └── main.ts
│   ├── public/
│   │   └── zB_Logo.png        # Branding-Logo (Login + Dashboard)
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

### 2026-03-27 - Audit-Log (persistent, vollständig integriert)
- `backend/app/audit.py`: `AuditAction` Enum + `log_action()` — typsicher, kein Freitext in Routen.
- `backend/app/database.py`: `AuditLog`-Modell (timestamp/username/action/target/detail/success, alle mit Index).
- `backend/app/schemas.py`: `AuditLogResponse` Pydantic-Schema.
- `backend/app/routers/audit_routes.py`: `GET /api/audit` (JWT-geschützt, filter via query params: username/action/success/limit).
- `backend/app/main.py`: `audit_routes` Router eingebunden.
- `auth_routes.py`: Login-Erfolg (`login_success`) und Login-Fehler (`login_failed`) protokolliert.
- `room_routes.py`: Internet-Toggle (`internet_toggle`) protokolliert.
- `whitelist_routes.py`: Erstellen/Aktualisieren/Löschen/Toggle protokolliert.
- `backend/tests/test_audit.py`: Unit- und API-Tests für `log_action()` und `GET /api/audit`.
- `frontend/src/api.ts`: `AuditEntry`-Interface + `auditApi.getAuditLogs()`.
- `frontend/src/constants/copy.ts`: `copy.audit.*` — alle Texte zentral.
- `frontend/src/components/dashboard/AuditLog.vue`: Tabelle neueste-zuerst, Filter-Ready, Badges OK/Fehler, Zeitformatierung CH.
- `frontend/src/components/Dashboard.vue`: "Protokoll"-Button rechts im Header öffnet `AuditLog`-Modal.

### 2026-03-27 - Frontend Architektur (pitch-tauglich, ohne Vendor-Dump)
- **Kein** `tailwind-plus`-Ordner im App-Repo: keine hunderten ungenutzten UI-Dateien; bei Bedarf externe Tailwind-UI-Referenz verlinken, nicht committen.
- `src/styles/tokens.css` + `base.css`: zentrale Design-Tokens; `main.ts` importiert nur `styles/base.css`.
- `src/constants/copy.ts`: sichtbare DE-Texte gebündelt.
- `components/ui/` (`UiButton`, `UiModal`), `components/layout/AppTopBar.vue`, `dashboard/WhitelistModal.vue`: klare Schichten, Darstellung unverändert zum letzten UI-Stand.

### 2026-03-27 - Dashboard Feintuning (Grid, Grün, Modularisierung)
- `frontend/src/components/dashboard/RoomCard.vue` + `DashboardPageTitle.vue`: Zimmerkarten und Titel ausgelagert.
- Dashboard: zweites Logo im Content entfernt (Logo nur noch im weissen Header).
- Raster: maximal 3 Spalten (1 / 2 / 3 je Viewport), breitere Karten; „Sperren“-Button in Status-Grün, schlankere Buttons.
- Design-Tokens: gemeinsame Status-Farben als CSS-Variablen (`--color-status-on-*`); später in `styles/tokens.css` konsolidiert.

### 2026-03-27 - Frontend UI Redesign (grün, logo-basiert)
- `frontend/public/zB_Logo.png`: neues zB-Branding im Projekt integriert.
- `frontend/src/App.vue` + globale Styles: neues Layout/Theme in Grün, Header mit Logo nach Login.
- `frontend/src/components/Login.vue`: Login visuell neu aufgebaut (Card-Layout mit Logo, klare Felder, gleiche Login-Logik).
- `frontend/src/components/Dashboard.vue`: Zimmer-Karten neu gestaltet; Whitelist-Verwaltung in Modal/Card direkt pro Zimmer (inkl. direkter Eingabe bei gesperrtem Zimmer), ohne API- oder Business-Logikänderung.
- Verifikation: `npm run build` im `frontend/` erfolgreich.

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
