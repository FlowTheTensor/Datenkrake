# Agentensystem (MCP, A2A, LAP)

Setzt auf dem bestehenden IoT-Stack (`../Raspberry/`) auf und ergänzt ihn
um drei Agentenprotokolle. Keine bestehende Komponente (Arduino UNO Q,
Mosquitto, MariaDB, Subscriber, Web-Dashboard) wird verändert oder ersetzt.

- **MCP** – `../MCPLokalClaudDesktop/mcpserver.py` (erweitert, siehe dortiger Commit) für Claude Desktop
- **A2A** – `db_agent/`, `orchestrator_agent/`, `report_agent/`
- **LAP** – `lap_common/`, `wartungs_agent/`

## Was neu dazukommt

| Neu | Ersetzt/ergänzt |
|---|---|
| `../MCPLokalClaudDesktop/mcpserver.py` | **erweitert** (alle 5 bestehenden Tools unverändert) um 1 Tool, 2 Resources, 1 Prompt |
| `../Raspberry/mariadb/init/01-agentensystem.sql` | **ergänzt** `00-create-database.sql` um 2 Tabellen + 1 User |
| `../Raspberry/web/leitstand.html` | **ergänzt** `index.php` um eine zweite, verlinkte Seite |
| `anomalie_poller/` | überbrückt die im Haupt-README unter "Nächste Schritte" genannten offenen Punkte "Echtzeit-Inferenz" / "Alarm-System" |
| `wartungs_agent/`, `lap_common/` | LAP-Instrument-Agent |
| `db_agent/`, `orchestrator_agent/`, `report_agent/` | A2A-Schicht |
| `shared/` | gemeinsame DB-Zugriffsschicht (kennt weder MCP noch A2A noch LAP) |

## Setup

1. SQL-Migration einspielen (bei Neuinstallation läuft sie automatisch mit):
   ```bash
   mysql -h <pi-ip> -P 3306 -u root -p telemetry < ../Raspberry/mariadb/init/01-agentensystem.sql
   ```
2. Claude Desktop neu starten, damit die erweiterte `mcpserver.py` greift (Konfiguration bleibt wie im Haupt-README beschrieben).
3. Python-Umgebung für den Agenten-Teil (auf einem Rechner mit Netzzugriff auf `datenkrake.local`):
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Prozesse und Reihenfolge

| # | Befehl | Rolle | Port |
|---|---|---|---|
| 1 | *(bestehende Pipeline: Arduino UNO Q, Mosquitto, MariaDB, Subscriber)* | liefert `audio_spectrum` | – |
| 2 | `python -m anomalie_poller.poller` | füllt `audio_anomalien` (Übergangslösung) | – |
| 3 | `python -m wartungs_agent` | LAP-Server | 9101 |
| 4 | `python -m db_agent` | A2A-Server | 9999 |
| 5 | `python -m report_agent` | A2A-Server | 9201 |
| 6 | `python -m orchestrator_agent` | A2A-Server + Überwachungsschleife | 9200 |

3–5 vor 6 starten. Alle Befehle aus `Agentensystem/` heraus ausführen.

## Kette im Überblick

**Arduino UNO Q → MQTT → MariaDB `audio_spectrum`** *(unverändert, bestehend)*
**→ `anomalie_poller`** *(neu, Platzhalter für künftige Echtzeit-Inferenz)*
**→ `audio_anomalien`** *(neu)*
**→ Orchestrator-Agent (A2A) erkennt offene Fälle → delegiert per LAP an Wartungs-Agent → Report-Agent (A2A) meldet**

Parallel dazu unverändert: **MariaDB → PHP-Dashboard** (`../Raspberry/web/index.php`) und **MariaDB → MCP-Server → Claude Desktop**.

## Leitstand-Dashboard

`../Raspberry/web/leitstand.html` ist eine zweite, statische Seite im
selben Web-Container (wird von Apache automatisch mit ausgeliefert,
keine Änderung am Dockerfile nötig). Sie zeigt Agent-/Instrument-Cards,
das Architektur-Diagramm, einen LLM-Chat (LM Studio) sowie eine
A2A-Konsole. Erreichbar unter `http://datenkrake.local/leitstand.html`,
verlinkt von `index.php` aus.

Live-Abrufe der Agent-Cards funktionieren nur, wenn die Agenten CORS für
den Browser-Ursprung erlauben (Standard-FastAPI/Starlette tut das nicht
automatisch) – siehe Hinweis im Dashboard selbst.

## Wichtige Einschränkung: noch keine Stationszuordnung

Das aktuelle Schema kennt nur EIN überwachtes Objekt (ein Arduino UNO Q,
ein Mikrofon). Sobald mehrere Arduino UNO Q an verschiedenen Stationen
betrieben werden, braucht `audio_spectrum` eine zusätzliche Spalte (z. B.
`station`), die dann durch `shared/db_service.py`, `anomalie_poller/`,
`orchestrator_agent/monitor.py` und `wartungs_agent/` durchgereicht wird.

## Abgrenzung fürs Tafelbild

| | MCP | A2A | LAP |
|---|---|---|---|
| Verbindet | Agent ↔ Daten | Agent ↔ Agent | Agent ↔ physisches Zusatzgerät |
| Hier konkret | `mcpserver.py` für Claude Desktop | Orchestrator ↔ DB-Agent, Orchestrator ↔ Report-Agent | Orchestrator → Wartungs-Agent |
| Einheit | Tool-Aufruf / Resource-Read / Prompt-Auswahl | Task mit Lebenszyklus | Reservation → (Safety-Fence) → MeasurementResult |

## Ehrlicher Hinweis zu LAP

Für LAP gibt es (Stand Juli 2026) kein offizielles, verbreitetes SDK – das
Protokoll stammt aus einer sehr jungen Forschungsarbeit (Zhu et al., Juni
2026, arXiv:2606.03755). `lap_common/base.py` ist eine didaktische
Nachbildung der vier Kernprimitive (InstrumentCard, Reservation,
Safety-Fence, MeasurementResult), keine zertifizierte Implementierung des
tatsächlichen Wire-Protokolls. Für MCP und A2A werden dagegen die
offiziellen Python-SDKs genutzt (`mcp`, `a2a-sdk`).

## Bekannte Vereinfachungen

- Safety-Fence-Bestätigung wird in der Demo automatisch erteilt (`orchestrator_agent/monitor.py`) statt von einer Aufsichtsperson – in echt hier ansetzen.
- `pruefe_akustik_anomalie()` (in `mcpserver.py` und `shared/db_service.py`) ist eine einfache Mittelwert/Standardabweichungs-Heuristik, kein trainiertes Modell.
- Der `orchestrator_agent` liest den Anomalie-Status aktuell direkt über `shared/db_service.py` statt über einen A2A-Hop zum `db_agent` (spart einen Netzwerk-Sprung in der Demo). Der `db_agent` bleibt trotzdem ein regulärer A2A-Server für andere Agenten oder Menschen, die ihn ansprechen wollen.
