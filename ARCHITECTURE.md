# Architektur — OnOffLine

## Übersicht

Web-App zur Steuerung des Internetzugangs in 7 Schulzimmern (VLANs) am zB. Zentrum Bildung Baden.

```
┌──────────────────────────────────────────────────┐
│  Frontend (Vue 3 + TypeScript)                   │
│  Nginx auf Port 80                               │
└──────────────────┬───────────────────────────────┘
                   │ REST / JSON
┌──────────────────▼───────────────────────────────┐
│  Backend (FastAPI + SQLAlchemy)                   │
│  Port 8000                                       │
│  Auth: JWT (local oder LDAP)                     │
│  DB: SQLite                                      │
└──────┬───────────────────────────┬───────────────┘
       │                           │
       │ LDAP bind/search          │ HTTP PUT /rooms/policies
       │                           │
┌──────▼──────────┐   ┌───────────▼───────────────┐
│  OpenLDAP       │   │  Firewall Agent (FastAPI)  │
│  Port 389       │   │  Port 8080                 │
│  Testverzeichnis│   │  Driver: mock | shorewall  │
└─────────────────┘   └───────────┬───────────────┘
                                  │
                      ┌───────────▼───────────────┐
                      │  Shorewall + ipset         │
                      │  (Produktion)              │
                      │  7 VLANs: 18–22, 118–119   │
                      └───────────────────────────┘
```

## Komponenten

### Frontend

- **Stack:** Vue 3 + TypeScript, Vite als Build-Tool
- **Styling:** Custom CSS mit Design-Tokens (`tokens.css`), kein Framework
- **HTTP-Client:** Axios mit JWT-Interceptor
- **UI-Komponenten:** `UiButton`, `UiModal`, `UiConfirm`, `UiToast`
- **Deployment:** Multi-Stage Docker Build (Node → Nginx)

### Backend

- **Framework:** FastAPI mit SQLAlchemy ORM
- **Datenbank:** SQLite (einzelne Datei, Volume-Mount)
- **Auth:** JWT-Token (8h Gültigkeit), Login via Local-DB oder LDAP
- **Passwort-Hashing:** SHA-256 (lokale Accounts)
- **API-Prefix:** `/api/`
- **Scheduler:** Async-Loop (60s Intervall) für zeitgesteuerte Raumsperren

### Firewall Agent

- **Eigenständiger FastAPI-Service** auf dem Firewall-Host
- **Zwei Driver:**
  - `mock` — schreibt gerenderte Regeln als Dateien (Entwicklung)
  - `shorewall` — erzeugt Shorewall-Include-Regeln + ipset-Einträge (Produktion)
- **Kommunikation:** Backend → Agent via `PUT /rooms/policies` (Token-Auth)
- **Whitelist-Auflösung:** Hostnamen → IPv4 via DNS, dann ipset

### OpenLDAP

- Testverzeichnis mit vorkonfigurierten Lehrern
- Nur in Compose aktiv; Produktion nutzt das bestehende Schulverzeichnis

## Datenmodell

```
users
├── id, username, password_hash
└── vlan_id, room_name

rooms
├── id, name, subnet, vlan_id
├── internet_enabled
├── schedule_enabled, schedule_open_time, schedule_lock_time
└── manual_override_active, manual_override_enabled

whitelist_templates
├── id, name, urls (JSON)
└── ↔ room_whitelist_assignments (room_id, whitelist_id, is_active)

audit_logs
├── id, timestamp, username, action
└── target, detail (JSON), success
```

Whitelists sind als Templates gespeichert und werden pro Raum einzeln aktiviert/deaktiviert.

## Deployment

```yaml
# docker-compose.yml — 4 Services
frontend       → Nginx, Port 80
backend        → FastAPI, Port 8000
ldap           → OpenLDAP, Port 389
shorewall-mock → Firewall Agent, Port 8081
```

Alle Konfiguration über Umgebungsvariablen. SQLite und Firewall-State als Volume-Mounts.

## API-Endpunkte

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| POST | `/api/login` | Login (form-data) |
| GET | `/api/rooms` | Alle Räume mit Status |
| POST | `/api/rooms/{id}/toggle` | Internet ein/aus (setzt manuellen Override) |
| PUT | `/api/rooms/{id}/schedule` | Zeitplan konfigurieren |
| GET | `/api/whitelists` | Whitelists abrufen |
| POST | `/api/whitelists` | Whitelist erstellen |
| PUT | `/api/whitelists/{id}` | Whitelist bearbeiten |
| PATCH | `/api/whitelists/{id}/toggle` | Whitelist aktivieren/deaktivieren |
| DELETE | `/api/whitelists/{id}` | Whitelist löschen |
| GET | `/api/audit` | Audit-Log |
| GET | `/api/health` | Health-Check |

## Firewall-Synchronisation

Bei jeder Änderung (Toggle, Whitelist, Zeitplan) synchronisiert das Backend die **komplette Room-Policy** zum Firewall Agent:

```json
{
  "rooms": [{
    "vlan_id": 18,
    "subnet": "10.3.18.0/24",
    "internet_enabled": false,
    "whitelist_entries": ["google.com", "wikipedia.org"]
  }]
}
```

Der Agent rendert daraus Shorewall-Regeln und ipset-Einträge.

## Zeitsteuerung

- Pro Raum konfigurierbar: Sperrzeit (Lock) und Freigabezeit (Open)
- Backend prüft alle 60 Sekunden und bei jedem Room-Request
- Manueller Override überschreibt den Zeitplan bis zum Zurücksetzen
