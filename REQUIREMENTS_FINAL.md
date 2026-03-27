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

**User-Modell:**
- **1 Admin-User pro Zimmer** (7 User total)
- Jeder Admin kann **nur sein Zimmer** steuern
- Kein zentraler Super-Admin
- Harte User-Trennung

**Login-Flow:**
- User loggt sich ein
- Wird automatisch seinem Zimmer zugeordnet (via Username)
- Sieht nur sein Zimmer im Dashboard

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
- FastAPI (Python)
- nftables (Firewall-Rules pro VLAN)
- Squid (URL-Filtering)
- SQLite (User + Whitelist-Templates)

**Frontend:**
- React + Vite
- Minimales UI (Login, Dashboard, Whitelist-Manager)

**Deployment:**
- Nginx Reverse Proxy
- Systemd Services

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
POST /api/login          → JWT-Token
GET  /api/rooms          → Mein Zimmer (1 Eintrag)
POST /api/rooms/{id}/internet  → EIN/AUS
GET  /api/whitelists     → Templates
POST /api/whitelists     → Upload/Create
```

### 4. Frontend-Views
```
/login           → Login-Formular
/dashboard       → Zimmer-Status (Internet EIN/AUS Button)
/whitelist       → Whitelist-Manager (Upload/Edit)
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
