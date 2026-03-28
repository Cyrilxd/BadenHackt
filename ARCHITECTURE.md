# Internet EIN/AUS - Architektur

Dieses Dokument beschreibt die technische Zielarchitektur, die Komponenten, die Datenflüsse und die Verantwortlichkeiten der einzelnen Bausteine.

Das README enthält bewusst nur Setup-, Betriebs- und Nutzungsinformationen. Dadurch werden Redundanzen zwischen beiden Dokumenten vermieden.

## Architekturprinzipien

- Klare Trennung zwischen UI, Business-Logik, Persistenz und Firewall-Anbindung
- Zentrale Steuerung pro Raum statt manueller Eingriffe auf der Firewall
- Vollständige Policy-Synchronisation pro Raum statt inkrementeller Einzeländerungen
- Mock- und produktionsnahe Betriebsart über denselben Firewall-Agent
- Containerisierte Ausführung für reproduzierbares Deployment

## High-Level-Architektur

```text
┌─────────────────────────────────────────────────────┐
│  Frontend (Vue 3 + TypeScript, via Nginx)           │
└────────────────┬────────────────────────────────────┘
                 │ HTTP/REST
┌────────────────▼────────────────────────────────────┐
│  Backend (FastAPI + SQLAlchemy)                     │
│  Authentifizierung, Raumlogik, Persistenz           │
└────────────────┬────────────────────────────────────┘
                 │ HTTP room policy sync
┌────────────────▼────────────────────────────────────┐
│  Firewall-Agent (FastAPI)                           │
│  Driver: mock | shorewall                           │
└────────────────┬────────────────────────────────────┘
                 │ lokale Regelgenerierung / Apply
┌────────────────▼────────────────────────────────────┐
│  Firewall Host / Mock Runtime                       │
│  Regeln pro VLAN und Raum-Whitelist                 │
└─────────────────────────────────────────────────────┘
```

## Komponenten

### 1. Frontend

**Aufgabe**

- Login der Lehrpersonen
- Anzeige aller Räume
- Umschalten des Internetzugangs pro Raum
- Pflege der Whitelist pro Raum
- Anzeige von Lade- und Fehlerzuständen

**Technologie**

- Vue 3
- TypeScript
- Vite
- Axios
- TailwindCSS
- Nginx als Webserver

**Typische Routen**

- `/` für Login
- `/dashboard` für Raumübersicht und Steuerung

### 2. Backend

**Aufgabe**

- Authentifizierung via JWT und optional LDAP
- Verwaltung von Räumen und Whitelist-Einträgen
- Persistenz in SQLite
- Aggregation der Raum-Policy
- Synchronisation der Policy an den Firewall-Agent

**Technologie**

- FastAPI
- Uvicorn
- SQLAlchemy
- python-jose
- bcrypt

**Fachliche Verantwortung**

Das Backend ist die führende Instanz für den fachlichen Zustand eines Raums. Ein Raumzustand besteht mindestens aus:

- Raum-Metadaten
- `internet_enabled`
- aggregierter Whitelist

### 3. Firewall-Agent

**Aufgabe**

- Entgegennahme der vollständigen Raum-Policy vom Backend
- Übersetzung in Firewall-spezifische Regeln
- Schreiben oder Aktualisieren der resultierenden Konfiguration
- Anwendung der Regeln in `mock` oder `shorewall`

**Betriebsmodi**

- `mock`: für lokale Entwicklung und Demo
- `shorewall`: für den produktiven Betrieb auf einem Firewall-Host

### 4. Datenhaltung

**Aufgabe**

- Speicherung von Benutzer-, Raum- und Whitelist-Daten
- Persistente Grundlage für Authentifizierung und Raumzustände

**Technologie**

- SQLite

## Logische Datenobjekte

### Users

Speichert Benutzer und Authentifizierungsbezug.

Typische Felder:

- `id`
- `username`
- `password_hash`
- optional LDAP-bezogene Zuordnung

### Rooms

Speichert die fachliche Sicht auf die Schulzimmer.

Typische Felder:

- `id`
- `name`
- `subnet`
- `vlan_id`
- `internet_enabled`

### Whitelists

Speichert die Whitelist-Einträge pro Raum.

Typische Felder:

- `id`
- `name`
- `urls`
- `room_id`

## Zentrale Datenflüsse

### 1. Login

```text
Benutzer → Frontend → Backend
         → Prüfung gegen lokale Daten oder LDAP
         → JWT zurück an Frontend
```

### 2. Internet ein- oder ausschalten

```text
Benutzeraktion im Frontend
→ Backend aktualisiert Raumzustand
→ Backend erzeugt vollständige Raum-Policy
→ Firewall-Agent synchronisiert Regeln
→ Frontend erhält aktualisierten Status
```

### 3. Whitelist ändern

```text
Benutzeraktion im Frontend
→ Backend speichert oder ändert Whitelist-Eintrag
→ Backend aggregiert alle Einträge des Raums
→ vollständige Raum-Policy an Firewall-Agent
→ Firewall-Agent rendert und aktiviert Regeln
```

## Policy-Modell

Die Architektur folgt einem synchronisierten Zielzustand je Raum.

Das bedeutet:

- Es wird nicht nur eine Einzelaktion übertragen.
- Stattdessen wird pro Raum immer die vollständige Policy synchronisiert.
- Dadurch bleibt der Firewall-Zustand reproduzierbar und konsistent.

Eine Raum-Policy umfasst mindestens:

- Raumidentität
- VLAN oder Subnet-Bezug
- `internet_enabled`
- bereinigte, aggregierte Whitelist-Domains

## Normalisierung von Whitelist-Einträgen

Vor der Synchronisation werden Einträge vereinheitlicht.

Beispiele:

- `https://google.com/path` wird zu `google.com`
- `*.example.org` wird zu `example.org`

Dadurch kann der Firewall-Agent mit konsistenten Zielwerten arbeiten.

## Deployment-Sicht

Die Laufzeitumgebung basiert auf Docker Compose.

Typische Services:

- `frontend`
- `backend`
- `firewall-agent` oder Mock-Service
- unterstützende Infrastruktur wie LDAP-Testverzeichnis

Die konkrete Betriebsanleitung, Umgebungsvariablen und Startbefehle sind absichtlich nur im README dokumentiert.

## Sicherheitsüberlegungen

### Authentifizierung

- JWT für Session-basierte API-Zugriffe
- LDAP optional für zentrale Benutzerverwaltung

### Schnittstellenabsicherung

- Firewall-Agent über Token absichern
- Trennung von UI, Business-Logik und Firewall-Apply

### Betriebsrisiken

- Fehlerhafte Whitelist-Einträge werden vor der Synchronisation normalisiert
- Mock-Modus reduziert Risiken in Entwicklung und Demo
- Vollständige Policy-Synchronisation reduziert Drift zwischen Soll und Ist

## Erweiterungsmöglichkeiten

- Produktive LDAP-Integration
- Erweiterte Rollen und Berechtigungen
- Audit-Logging für Policy-Änderungen
- Historisierung von Raumzuständen
- Zusätzliche Firewall-Driver neben Shorewall
- Health Checks und Monitoring pro Komponente

