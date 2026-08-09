# Architektur-Update: Bundle

Enthält alle Änderungen an der Architekturabbildung in `leitstand.html`
(Branch `feature/agentensystem-mcp-a2a-lap`) plus die begleitende
Komponenten-Übersicht.

## Inhalt

- **`leitstand.html`** – fertige Datei, so wie sie im Repo liegen soll.
  Einfach die bestehende Datei im Repo-Root damit überschreiben.
- **`architektur-komponenten.md`** – eigenständige Markdown-Referenz aller
  Komponenten/Protokolle (kann z. B. unter `docs/` abgelegt werden;
  ihr Inhalt ist außerdem als Overlay direkt in `leitstand.html` eingebaut).
- **`architektur-update.patch`** – Git-Patch mit exakt denselben Änderungen,
  falls du sie lieber über `git apply`/`git am` statt Copy-Paste einspielen willst.

## Anwenden

**Variante A – Datei ersetzen (am einfachsten):**
```bash
cp leitstand.html /pfad/zu/deinem/repo/leitstand.html
cp architektur-komponenten.md /pfad/zu/deinem/repo/docs/architektur-komponenten.md   # optional
```

**Variante B – Patch einspielen:**
```bash
cd /pfad/zu/deinem/repo
git checkout feature/agentensystem-mcp-a2a-lap
git apply /pfad/zu/architektur-update.patch
# oder, falls du es als eigenen Commit willst:
git am /pfad/zu/architektur-update.patch   # falls als Mail-Patch exportiert; sonst:
git apply architektur-update.patch && git add leitstand.html && git commit -m "Architekturabbildung überarbeitet"
```

Der Patch ist ein reiner `git diff` gegen den aktuellen Stand von
`origin/feature/agentensystem-mcp-a2a-lap` (Stand: siehe Commit-Historie
zum Zeitpunkt der Erstellung). Falls der Branch seitdem weitergewandert
ist, kann `git apply` fehlschlagen — dann einfach Variante A nutzen.

## Was wurde geändert (Zusammenfassung)

1. Architektur-SVG komplett neu aufgebaut: drei Zonen
   (Datenerhebung / Verarbeiten + Bereitstellen / Analyse), alle Bausteine
   aus der Skizze ergänzt (Mosquitto, Node-RED, InfluxDB, Anomalie-Poller,
   Modellanlage, Data-Lake-Stack, MCP-Server, Browser, Webserver).
2. Zwei inhaltliche Korrekturen ggü. der ursprünglichen Skizze:
   - LAP zeigt vom Wartungs-Agent auf ein eigenes **Zusatzgerät**, nicht auf
     die Modellanlage/Produktionssteuerung.
   - MCP ist nur zwischen MCP-Server und den MCP-Clients beschriftet;
     die Verbindung MariaDB → MCP-Server heißt korrekt „SQL (Netzwerk)“.
3. Anomalie-Poller ruft zusätzlich Zeitreihenanalysen per Flux-Query aus
   InfluxDB ab.
4. Modellanlage-Box höher gesetzt, 10 Quadrate im Oval angeordnet
   (4 oben, 4 unten, je 1 links/rechts).
5. „SQL · offene Anomalien“-Pfeil so umgelenkt, dass er den DB-Agent-Pfeil
   nicht mehr kreuzt.
6. Neuer Pfeil Browser → Report-Agent (HTTP, Agenten-Konsole spricht die
   Agent Card direkt an).
7. Claude Desktop und Agent Harness als zwei gleichwertige, getrennte
   MCP-Clients dargestellt (statt einer verschachtelten Box).
8. Zwei Kürzel-Texte in der Modellanlage-/Node-RED-Box entfernt
   („nur lesend (OPC-UA)“, „OPC-UA → MQTT-Bridge“).
9. Die drei bidirektionalen SQL-Verbindungen (Anomalie-Poller, DB-Agent,
   Report-Agent ↔ MariaDB) haben jetzt Pfeilspitzen an beiden Enden,
   passend zur Beschreibung in der Komponenten-Übersicht.
10. Neues Overlay „Komponenten-Übersicht“: Button neben der
    „Architektur“-Überschrift öffnet eine Kartenansicht aller Bausteine
    mit farbcodierten Protokoll-Badges (MCP/A2A/LAP/MQTT-OPC-UA/Datenfluss),
    schließbar per ✕, Klick auf Hintergrund oder Escape.
