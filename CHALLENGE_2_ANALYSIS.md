# Challenge 2: IT-Security & Asset Intelligence - Analyse

**Auftraggeber:** Kromer Print AG (Lenzburg)  
**Coach:** Andreas Wüthrich, Global CIO & CISO

---

## Infrastruktur-Overview

**Bestand:**
- 23x Windows Server 2019 VMs
- 5x Linux Debian 11 VMs
- 10x Windows Laptops
- 4x Windows Clients

**Total: ~42 Assets** (mittelgroße Infrastruktur)

---

## Challenge-Typ: EVALUATION & VERGLEICH

**Nicht:** Live-Entwicklung  
**Sondern:** Tool-Research, Testing, Dokumentation, Präsentation

---

## 1. Schwachstellen-Scanning (Vulnerability Management)

### Tool-Kandidaten

#### **Greenbone (OpenVAS)** - Open Source
**Pro:**
- Komplett kostenlos (Community Edition)
- Sehr umfangreich (50.000+ NVTs)
- Authenticated Scans (Windows + Linux)
- REST API verfügbar
- Aktive Community

**Contra:**
- Setup komplex (Docker/VM nötig)
- UI etwas dated
- Support nur kommerziell (Greenbone Enterprise)

**Kosten:**
- Community: **0€**
- Enterprise: ~8.000-15.000€/Jahr (je nach Asset-Anzahl)

---

#### **Tenable Nessus** - Kommerziell
**Pro:**
- Marktführer, sehr ausgereift
- Einfaches Setup
- Exzellente Reporting-Features
- Windows/Linux/Cloud-Scans
- Guter Support

**Contra:**
- Teuer bei vielen Assets
- Vendor Lock-in

**Kosten:**
- Nessus Essentials: **Kostenlos** (bis 16 IPs)
- Nessus Professional: **~3.500€/Jahr** (unbegrenzt)
- Tenable.io: **~8.000-20.000€/Jahr** (SaaS, mehr Features)

---

#### **Weitere Optionen:**
- **Qualys VMDR** (Enterprise, Cloud-basiert, teuer)
- **Rapid7 InsightVM** (ähnlich Tenable, ~10.000€/Jahr)
- **Wazuh** (Open Source, eher Host-based IDS)

---

### Empfehlung für Kromer Print AG (42 Assets):

**Kurzfristig (Hackathon-Demo):**
- **Greenbone Community** aufsetzen
- Live-Scan durchführen (Demo-Umgebung)
- Report generieren

**Langfristig (Production):**
- **Nessus Professional** (3.500€/Jahr)
  - Grund: 42 Assets = mittelgroß, Budget vertretbar
  - Besserer Support als Greenbone Community
  - Einfacher für IT-Team (weniger Wartung)

**Budget-Option:**
- Greenbone Community + Paid Support (~2.000€/Jahr)

---

## 2. IT-Asset-Management & Systemsteuerung

### Tool-Kandidaten

#### **Snipe-IT** - Open Source
**Pro:**
- Kostenlos
- Einfaches Asset-Tracking (Hardware, Software, Lizenzen)
- REST API
- QR-Code-Labels
- Aktive Entwicklung

**Contra:**
- **KEIN** Deployment/Update-Management
- Nur Inventar, keine Steuerung
- Manuelles Eintragen (oder API-Integration nötig)

**Kosten:** 0€ (Self-hosted)

---

#### **GLPI + FusionInventory** - Open Source
**Pro:**
- Kostenlos
- Ticketing + Asset-Management
- Auto-Inventarisierung (Agent-basiert)
- Plugin-Ökosystem
- ITIL-konform

**Contra:**
- Setup komplex
- UI outdated
- **Limitiertes** Deployment (via Plugins möglich, aber nicht Kern-Feature)

**Kosten:** 0€

---

#### **OCS Inventory NG** - Open Source
**Pro:**
- Kostenlos
- Auto-Discovery (Agent-basiert)
- Windows + Linux
- Deployment-Module (via Plugins)

**Contra:**
- Weniger aktiv entwickelt
- UI sehr dated

**Kosten:** 0€

---

#### **PDQ Deploy + PDQ Inventory** - Kommerziell (Windows-only)
**Pro:**
- **Exzellent** für Windows-Umgebungen
- Software-Deployment (Push)
- Windows-Update-Management
- Sehr einfache Bedienung
- Gutes Preis-/Leistungsverhältnis

**Contra:**
- **Nur Windows** (keine Linux-Server)
- Keine Web-UI (Client-Software nötig)

**Kosten:**
- PDQ Deploy: ~500€/Jahr (Single-User)
- PDQ Inventory: ~500€/Jahr
- Bundle: **~800€/Jahr**

---

#### **ManageEngine Desktop Central** - Kommerziell
**Pro:**
- All-in-One (Asset-Management + Deployment + Patch-Management)
- Windows + Mac + Linux
- Web-basiert
- Umfangreiches Reporting

**Contra:**
- Teuer bei vielen Assets
- Komplex (Overkill für 42 Assets?)

**Kosten:**
- Free Edition: **25 Endpoints kostenlos**
- Professional: **~2.500-4.000€/Jahr** (50 Endpoints)

---

#### **Lansweeper** - Kommerziell
**Pro:**
- Sehr gute Auto-Discovery (agentless + agent-based)
- Asset-Tracking + Software-Inventar
- **Kein Deployment**, aber exzellente Übersicht
- Netzwerk-Device-Scanning

**Contra:**
- Teuer
- Deployment/Patch-Management separat

**Kosten:**
- Starter: **~1.500€/Jahr** (100 Assets)
- Pro: **~3.500€/Jahr**

---

#### **Tactical RMM** - Open Source (RMM = Remote Monitoring & Management)
**Pro:**
- **Kostenlos**
- Agent-basiert (Windows + Linux)
- Remote-Control (via MeshCentral)
- Script-Deployment
- Patch-Management (via Chocolatey/Winget)
- Aktive Community

**Contra:**
- Noch relativ jung (seit 2020)
- Self-hosted (Setup-Aufwand)

**Kosten:** 0€ (Cloud-Hosting ~5€/Monat optional)

---

### Empfehlung für Kromer Print AG:

**Option 1: Open Source (Budget-optimiert)**
- **Tactical RMM** (kostenlos)
  - Inventar + Deployment + Patch-Management
  - Windows + Linux
  - Self-hosted

**Option 2: Hybrid (Best-of-Both)**
- **Lansweeper** (~1.500€/Jahr) → Asset-Übersicht
- **PDQ Deploy** (~800€/Jahr) → Windows-Deployment
- **Ansible** (kostenlos) → Linux-Deployment

**Total: ~2.300€/Jahr**

**Option 3: All-in-One (Kommerziell, einfachste Lösung)**
- **ManageEngine Desktop Central Free** (25 Assets kostenlos)
- + **Professional** für restliche 17 Assets (~2.500€/Jahr)

**Total: ~2.500€/Jahr**

---

## 3. Synergien: Vulnerability + Asset-Management

### Integration-Möglichkeiten:

**Schwachstellen-Scan → Asset-DB:**
- Greenbone/Nessus erkennt Assets via Network-Scan
- Export (CSV/JSON) → Import in Asset-Management-Tool
- **Problem:** Manuelle Synchronisation nötig (kein Auto-Sync)

**Bessere Lösung:**
- Asset-Management-Tool mit **integriertem Vuln-Scan**:
  - **Tenable.io** (Asset-Discovery + Vuln-Scan in einem)
  - **Qualys VMDR** (gleiches Konzept)
  - **Wazuh** (Open Source, Host-based)

**Für Kromer Print AG:**
- Separate Tools (Nessus + Tactical RMM/Lansweeper)
- Grund: Kosten/Nutzen besser als All-in-One-Enterprise-Lösung

---

## 4. Sicherheit & Datenschutz

### Greenbone/Nessus:
- Authenticated Scans → Admin-Credentials nötig (Risiko!)
- Empfehlung: Dedizierter Scan-User mit Read-Only-Rechten

### Asset-Management (Agent-basiert):
- Agents benötigen Admin-Rechte
- Kommunikation verschlüsselt (TLS)
- Self-hosted → Daten bleiben im Haus (DSGVO-konform)

---

## 5. Skalierung

**Aktuell: 42 Assets**  
**Wachstum: +20-50% (→ 50-60 Assets in 2-3 Jahren?)**

### Skalierbarkeit:
- **Greenbone/Nessus:** Linear skalierbar (mehr Scan-Zeit)
- **Tactical RMM:** Problemlos bis 500+ Assets
- **PDQ Deploy:** Bis ~200 Devices kein Problem
- **ManageEngine:** Enterprise-Ready (1000+ Assets)

**Empfehlung:** Tactical RMM oder ManageEngine wachsen mit.

---

## 6. Kostenvergleich (Total Cost of Ownership, 3 Jahre)

| Szenario | Jahr 1 | Jahr 2-3 (p.a.) | Total (3J) |
|----------|--------|------------------|------------|
| **Open Source (Greenbone + Tactical RMM)** | 0€ (Setup-Zeit) | 0€ | **0€** |
| **Budget (Nessus Prof. + Tactical RMM)** | 3.500€ | 3.500€ | **10.500€** |
| **Hybrid (Nessus + Lansweeper + PDQ)** | 5.800€ | 5.800€ | **17.400€** |
| **All-in-One (Nessus + ManageEngine)** | 6.000€ | 6.000€ | **18.000€** |
| **Enterprise (Tenable.io + ManageEngine Pro)** | 12.000€ | 12.000€ | **36.000€** |

---

## 7. Finale Empfehlung für Kromer Print AG

### Variante A: **Budget-optimiert** (0-500€/Jahr)
**Tools:**
- Greenbone Community (Vuln-Scan)
- Tactical RMM (Asset-Management + Deployment)

**Pro:** Kostenlos, skalierbar  
**Contra:** Mehr Setup-Aufwand, Community-Support

---

### Variante B: **Balanced** (Empfohlen, ~4.000€/Jahr)
**Tools:**
- Nessus Professional (~3.500€/Jahr)
- Tactical RMM (kostenlos) ODER ManageEngine Free (25) + Pro (17)

**Pro:** Professioneller Vuln-Scan, guter Support, trotzdem erschwinglich  
**Contra:** Tactical RMM Self-hosting nötig

---

### Variante C: **Enterprise-Ready** (~10.000€/Jahr)
**Tools:**
- Tenable.io (~8.000€/Jahr)
- ManageEngine Desktop Central Pro (~3.000€/Jahr)

**Pro:** Alles aus einer Hand, bester Support  
**Contra:** Teuer für 42 Assets

---

## 8. Hackathon-Umsetzung (1 Tag)

### Was machbar ist:

**Vormittag (4h):**
1. Greenbone VM aufsetzen (Docker/VM)
2. Nessus Essentials installieren (parallel)
3. Demo-Scan laufen lassen (interne VMs)

**Nachmittag (4h):**
1. Tactical RMM installieren (Demo-Server)
2. Agents auf 2-3 Test-VMs deployen
3. Asset-Inventar auslesen
4. Report/Präsentation vorbereiten

### Deliverables:
- ✅ Vergleichs-Tabelle (Excel/Markdown)
- ✅ Live-Demo (Greenbone + Tactical RMM)
- ✅ Empfehlung mit Kostenanalyse
- ✅ Präsentation (15 Min)

---

## 9. Vergleich zu Challenge 1

| Kriterium | Challenge 1 (Internet ein/aus) | Challenge 2 (Security/Asset) |
|-----------|-------------------------------|------------------------------|
| **Typ** | Entwicklung (Custom-Software) | Evaluation (Tool-Vergleich) |
| **Code** | Viel (Backend + Frontend) | Wenig (Setup-Scripts) |
| **Risiko** | Hoch (funktioniert Demo?) | Niedrig (Tools laufen) |
| **Lernkurve** | Backend-Entwicklung, nftables | Tool-Installation, Testing |
| **Präsentation** | Live-Demo (kritisch) | Report + Screenshots |
| **Impact** | Direkt nutzbar (wenn fertig) | Entscheidungsgrundlage |

---

## 10. Meine Einschätzung

**Challenge 2 ist "sicherer" für Hackathon:**
- Weniger Risiko (Tools funktionieren garantiert)
- Fokus auf Analyse/Bewertung statt Entwicklung
- Mehrwert: Klare Kaufempfehlung für Auftraggeber

**Challenge 1 ist "spannender" für Entwickler:**
- Custom-Code, eigene Architektur
- Mehr technische Tiefe
- Aber: Höheres Risiko, dass nicht alles funktioniert

---

**Was bevorzugst du?** Oder soll ich beide Challenges parallel vorbereiten?
