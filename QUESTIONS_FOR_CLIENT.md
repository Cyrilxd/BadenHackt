# Fragen an Auftraggeber - zB. Zentrum Bildung

## 1. NETZWERK-ARCHITEKTUR (KRITISCH)

### Gateway/Router Setup
- [ ] Ist der Linux-Server das **Gateway/Router** für alle Schulzimmer?
- [ ] Oder läuft er **transparent** im Netz und muss Traffic umleiten?
- [ ] Sind die 7 Subnetze bereits getrennt (VLANs/physisch)?
- [ ] Beispiel Subnetz-Schema: `192.168.10.0/24` für Zimmer 1?

### DNS-Routing
- [ ] Läuft DNS zentral über den Linux-Server?
- [ ] Oder nutzen die PCs externe DNS (z.B. ISP)?
- [ ] Können wir DNS-Anfragen zentral filtern?

---

## 2. BERECHTIGUNGEN & ZUGRIFFSRECHTE

### Lehrer-Rollen
- [ ] Kann jede Lehrperson **nur ihr Zimmer** steuern?
- [ ] Oder gibt es Admins, die **alle Zimmer** steuern können?
- [ ] Wird das Zimmer beim Login automatisch erkannt (z.B. via IP)?

### Login-System
- [ ] Gibt es ein bestehendes SSO/LDAP/AD für Lehrer?
- [ ] Oder soll das System eigene Logins verwalten?

---

## 3. WHITELIST-DETAILS

### URL-Granularität
- [ ] Reichen **Domains** (`*.google.com`)? 
- [ ] Oder braucht es auch **Subpaths** (`example.com/education/*`)?
- [ ] Wildcard-Regeln erlaubt? (z.B. `*.edu`, `*.gov`)

### Standard-Whitelists
- [ ] Gibt es interne Ressourcen, die **immer** erreichbar sein müssen?
  - Schulserver? (`intranet.zb.ch`)
  - Office 365? Google Workspace?
  - Lernplattformen? (Moodle, Teams, etc.)

### Templates
- [ ] Gibt es vordefinierte Listen, die wir vorbereiten sollen?
  - "Recherche" (Wikipedia, News, etc.)
  - "Office" (Google Docs, Office 365)
  - "Programmieren" (GitHub, StackOverflow)

---

## 4. ZEITPLÄNE

### Stundenplan-Integration
- [ ] Gibt es einen **digitalen Stundenplan** (iCal, CSV, API)?
- [ ] Oder werden Zeitpläne **manuell** im GUI hinterlegt?
- [ ] Beispiel: "Montag 08:00-10:00 in Zimmer 3 → Internet gesperrt"

### Feinheiten
- [ ] Soll die Sperrung **hart** sein (sofortige Trennung)?
- [ ] Oder **soft** (Warnung, dann Sperrung nach X Minuten)?

---

## 5. BESTEHENDE INFRASTRUKTUR

### Alte Lösung
- [ ] Läuft die alte Shorewall-Lösung **parallel** während der Migration?
- [ ] Können wir das alte System als **Fallback** nutzen?
- [ ] Wer hostet den Linux-Server? (On-Premise, Datacenter, Cloud?)

### Hardware
- [ ] Welche Linux-Distribution läuft aktuell? (Debian, Ubuntu?)
- [ ] CPU/RAM/Specs des Servers?
- [ ] Gibt es redundante Server (HA-Setup)?

---

## 6. MONITORING & LOGGING

### Transparenz
- [ ] Sollen Lehrer sehen, **welche Schüler-PCs** aktiv sind?
- [ ] Sollen gesperrte Zugriffsversuche geloggt werden?
- [ ] Benachrichtigung, wenn Zeitplan aktiviert wird?

---

## 7. EDGE CASES & SPEZIALFÄLLE

### Notfall-Override
- [ ] Gibt es eine **Notfall-Freigabe** (z.B. für IT-Support)?
- [ ] Soll ein Admin alle Sperren sofort aufheben können?

### Schüler-Umgehung
- [ ] Nutzen Schüler **VPNs** oder **Proxy-Umgehungen**?
- [ ] Soll das System bekannte VPN-Domains blockieren?

### Mobile Devices
- [ ] Gibt es **BYOD** (Schüler-Smartphones/-Tablets)?
- [ ] Oder nur fixe Windows-PCs?

---

## 8. TIMELINE & DEPLOYMENT

### Zeitplan
- [ ] Wann soll das System **live** gehen? (Deadline?)
- [ ] Gibt es einen **Testlauf** in einem Zimmer?

### Schulung
- [ ] Brauchen Lehrer eine **Einführung**?
- [ ] Gibt es **Dokumentation** (Benutzerhandbuch)?

---

## 9. NICE-TO-HAVE FEATURES

### Zusatzfunktionen
- [ ] Soll es **Statistiken** geben? (z.B. "Wie oft wurde gesperrt?")
- [ ] Push-Benachrichtigungen bei Zeitplan-Aktivierung?
- [ ] Mobile App für Lehrer?

---

## PRIORITÄT-MATRIX

### MUST-HAVE (Blocker, wenn unklar)
1. ✅ Netzwerk-Architektur (Gateway vs. transparent)
2. ✅ DNS-Setup (zentral vs. extern)
3. ✅ Berechtigungen (Zimmer-Zuordnung)

### SHOULD-HAVE (beeinflussen Design)
4. ✅ Whitelist-Granularität (Domain vs. Subpath)
5. ✅ Stundenplan-Integration (API vs. manuell)
6. ✅ Bestehende Infrastruktur (Migration vs. parallel)

### NICE-TO-HAVE (später klärbar)
7. Monitoring/Logging
8. Edge Cases (VPN-Blocking, Notfall-Override)
9. Zusatzfeatures (Statistik, Mobile App)

---

**Ziel:** Top 6 Fragen innerhalb der ersten 30 Minuten klären, dann sofort mit Entwicklung starten! 🦇
