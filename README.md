# OPC-UA-Dokumentations-Overlay: Bundle

Ergänzt `leitstand.html` (Branch `feature/agentensystem-mcp-a2a-lap`) um ein
zweites Overlay für `UAExpertExport/Dokumentation_OPC_UA_Stationen.md`.

## Inhalt

- **`leitstand.html`** – fertige Datei, ersetzt die aktuelle im Repo-Root.
- **`uax-overlay.patch`** – reiner `git diff`, getestet gegen einen frischen
  Klon von `feature/agentensystem-mcp-a2a-lap` (`git apply --check` lief
  sauber durch).

## Anwenden

```bash
# Variante A – Datei ersetzen
cp leitstand.html /pfad/zu/deinem/repo/leitstand.html

# Variante B – Patch einspielen
cd /pfad/zu/deinem/repo
git apply /pfad/zu/uax-overlay.patch
git add leitstand.html && git commit -m "OPC-UA-Dokumentations-Overlay ergänzt"
```

## Was wurde ergänzt

- Button **„OPC-UA-Signaldokumentation“** im Node-RED-Panel bei
  **Thema D — Kommunikation & Industrie 4.0**.
- Neues Vollbild-Overlay mit dem kompletten Inhalt von
  `UAExpertExport/Dokumentation_OPC_UA_Stationen.md`:
  - Sprungnavigation (Stationen, Grundstruktur, Namenskonventionen,
    Signalgruppen, Stationsdetails, MQTT-Modell, Datenbankmodell,
    Sampling, KPI, Besonderheiten, Umsetzung, Dateien)
  - Stationstabelle (Endpoint, Datensätze)
  - Kartenraster für die 10 Stationen mit Charakteristik + Nutzen
  - MQTT-Topic-Schema und formatiertes JSON-Beispiel
  - Datenbankmodell (opc_raw, opc_mes_snapshot, opc_alarm_events)
  - Datei-Links (relativ, verweisen auf `UAExpertExport/…`, inkl.
    URL-Encoding für Leerzeichen/Umlaute)
- Schließen per ✕, Klick auf Hintergrund oder Escape — gleiches Verhalten
  wie beim bestehenden Architektur-Overlay; Öffnen/Schließen-Logik wurde
  dafür in eine gemeinsame `setupOverlay()`-Funktion refaktoriert, die
  jetzt für beide Overlays verwendet wird.
- Kein externes JS/CSS, alles inline in der bestehenden Datei.

## Hinweis zu den Datei-Links

Die Links im Abschnitt „Dateien“ zeigen relativ auf
`UAExpertExport/<Datei>`. Das funktioniert nur, wenn `leitstand.html`
und der Ordner `UAExpertExport/` im selben Verzeichnis ausgeliefert
werden (so wie aktuell im Repo-Root der Fall).
