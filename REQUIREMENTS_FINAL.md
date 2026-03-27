# Challenge 1: Finale Requirements

## Netzwerk-Architektur

**Setup:**
```
Internet → Firewall → Perimeter Firewall (unser Server) → 7 VLANs
```

**VLANs (Schulzimmer):**
- Vlan 18: 10.3.18.0/24
- Vlan 19: 10.3.19.0/24
- Vlan 20: 10.3.20.0/24
- Vlan 21: 10.3.21.0/24
- Vlan 22: 10.3.22.0/24
- Vlan 118: 10.3.118.0/24
- Vlan 119: 10.3.119.0/24

**DNS:**
- Pro Schulzimmer eigener DNS
- Wir arbeiten mit IPs (nicht DNS-basiert)

---

## Berechtigungen

**User-Modell (v2.0 - aktuell implementiert):**
- **3 Test-User** (lehrer, mueller, schmidt)
- Jeder Lehrer kann **alle 7 Zimmer** steuern
- Kein Zimmer-Binding — volle Flexibilität
- Whitelists sind **pro Zimmer** gespeichert

**Login-Flow:**
- User loggt sich ein
- Sieht **alle 7 Zimmer** im Dashboard (Grid-Ansicht)
- Kann jedes Zimmer steuern (Internet EIN/AUS)

---

## Whitelist

**Granularität:**
- **Domains reichen** (`google.com`, `wikipedia.org`)
- **ABER:** Müssen als URLs angegeben werden (wegen Squid/URL-Filter)
- Beispiel: `https://google.com`, `*.wikipedia.org`

**Templates:**
- **Keine** vordefinierten Standard-Whitelists
- **Eine Whitelist-Liste** via Config-File oder Text-File
  - Format: TXT/JSON (eine URL pro Zeile)
  - Lehrer kann eigene Listen hochladen/erstellen

---

## Zeitpläne

**Status:** ❌ **NICHT nötig** (nach Austausch entschieden)
- Kein Zeitplan-Feature im MVP
- Optional für später

---

## Alte Lösung

**Shorewall + Apache GUI:**
- Läuft parallel während Entwicklung
- Wird nach Hackathon ersetzt
- Gleiche Hardware (Linux Debian)

---

## MVP-Features (Hackathon)

### MUST-HAVE:
1. ✅ Login (7 User, je 1 pro Zimmer)
2. ✅ Internet EIN/AUS pro Zimmer
3. ✅ URL-Whitelist (Domain-basiert)
4. ✅ Whitelist-Templates (Config-File)
5. ✅ Einfaches Web-GUI

### NICE-TO-HAVE:
- Logging (welche URLs geblockt)
- Status-Anzeige (wie viele PCs aktiv)
- ~~Zeitpläne~~ (später)

---

## Tech-Stack (Final)

**Backend:**
- FastAPI (Python 3.11)
- nftables (Firewall-Rules pro VLAN)
- SQLite (User + Rooms + Whitelist-Templates)
- SQLAlchemy 2.0 (ORM)
- JWT Auth (python-jose + bcrypt)

**Frontend:**
- Vue 3 + TypeScript + Vite
- Axios (HTTP-Client)
- Composition API + SFC
- Minimales UI (Login, Dashboard, Whitelist-Manager)

**Deployment:**
- Docker Compose
- Nginx Reverse Proxy (Frontend-Container)

---

## Umsetzung

### 1. Firewall-Logik (nftables)
```bash
# Zimmer 18 sperren:
nft add rule inet filter forward ip saddr 10.3.18.0/24 drop

# Zimmer 18 freigeben:
nft delete rule inet filter forward handle <handle>
```

### 2. URL-Whitelist (Squid)
```squid
# squid.conf per VLAN
acl vlan18 src 10.3.18.0/24
acl whitelist_vlan18 dstdomain .google.com .wikipedia.org
http_access allow vlan18 whitelist_vlan18
http_access deny vlan18
```

### 3. Backend-Endpoints
```
POST /api/login               → JWT-Token
GET  /api/rooms               → Alle 7 Zimmer
POST /api/rooms/{id}/toggle   → Internet EIN/AUS
GET  /api/whitelists           → Templates (opt. ?room_id=)
POST /api/whitelists           → Create
DELETE /api/whitelists/{id}    → Delete
GET  /api/health               → Health Check
```

### 4. Frontend-Views
```
SPA (Single Page Application):
- Login-Formular (nicht authentifiziert)
- Dashboard mit Zimmer-Grid + Whitelist-Manager (authentifiziert)
```

---

## Timeline (Hackathon)

**09:00-10:00:** Setup finalisieren
**10:00-12:00:** Backend API + nftables
**12:00-13:00:** Squid Whitelist-Integration
**13:00-15:00:** Frontend GUI
**15:00-16:30:** Testing + Bugfixes
**16:30-17:00:** Demo-Prep

---

**Status:** Requirements klar, ready to code! 🦇
