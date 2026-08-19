<img align="right" src="../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# Agentensystem (MCP, A2A, LAP)

Setzt auf dem bestehenden IoT-Stack (`../Raspberry/`) auf und ergänzt ihn
um drei Agentenprotokolle. Keine bestehende Komponente (Arduino UNO Q,
Mosquitto, MariaDB, Subscriber, Web-Dashboard) wird verändert oder ersetzt.

- **MCP** – `../MCPLokalClaudDesktop/mcpserver.py` (erweitert, siehe dortiger Commit) für Claude Desktop
- **A2A** – `db_agent/`, `orchestrator_agent/`, `report_agent/`
- **LAP** – `lap_common/`, `wartungs_agent/`
- **Agent Harness** – `agent_harness/`, zeigt die Tool-Aufruf-Schleife, die aus einem lokalen LLM (LM Studio) einen Agenten macht, der die MCP-Tools von oben selbst nutzt. Didaktische Einordnung: [`agent_harness/README.md`](agent_harness/README.md).

## Was neu dazukommt

| Neu | Ersetzt/ergänzt |
| --- | --- |
| `../MCPLokalClaudDesktop/mcpserver.py` | **erweitert** (alle 5 bestehenden Tools unverändert) um 1 Tool, 2 Resources, 1 Prompt |
| `../Raspberry/mariadb/init/01-agentensystem.sql` | **ergänzt** `00-create-database.sql` um 2 Tabellen + 1 User |
| `../Raspberry/web/index.html` | **ergänzt** die getrennten Audio- und PLC-Datenübersichten um den Leitstand |
| `anomalie_poller/` | überbrückt die im Haupt-README unter "Nächste Schritte" genannten offenen Punkte "Echtzeit-Inferenz" / "Alarm-System" |
| `wartungs_agent/`, `lap_common/` | LAP-Instrument-Agent |
| `db_agent/`, `orchestrator_agent/`, `report_agent/` | A2A-Schicht |
| `shared/` | gemeinsame DB-Zugriffsschicht (kennt weder MCP noch A2A noch LAP) |
| `agent_harness/` | zeigt, was ein LLM erst zum "Agenten" macht (die Tool-Aufruf-Schleife) – nutzt die MCP-Tools von oben, getestet gegen den echten `mcpserver.py` |

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

## Umgebungsvariablen (.env)

Im Ordner `Agentensystem/` liegt eine Vorlage: `.env.example`.

1. Kopieren und anpassen:

   ```bash
   cp .env.example .env
   ```

   PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Relevante Schalter:
   - `ANOMALIE_QUELLE=influx` (Standard) liest die Referenzwerte aus InfluxDB.
   - `ANOMALIE_QUELLE=mariadb` nutzt das bisherige Verhalten direkt auf `audio_spectrum`.
   - `REPORT_USE_LLM=true` aktiviert optional LLM-Formulierung im Report-Agent.
   - `REPORT_USE_LLM=false` nutzt das feste, offline-faehige Template (Standard).
3. Wichtig zur Architektur:
   - Erkennung kann aus Influx kommen, der Poller schreibt trotzdem in `audio_anomalien` (MariaDB).
   - Dadurch bleiben Orchestrator-, Wartungs- und Reporting-Kette unverändert kompatibel.
   - Report-Antworten gehen nur dann in ein LLM, wenn `REPORT_USE_LLM=true` gesetzt ist.

Mindestens diese Variablen muessen gesetzt sein:

```dotenv
ANOMALIE_QUELLE=influx

DK_DB_HOST=datenkrake.local
DK_DB_PORT=3306
DK_DB_NAME=telemetry
DK_READ_USER=mcp_read
DK_READ_PASSWORD=...
DK_WRITE_USER=anomalie_writer
DK_WRITE_PASSWORD=...

DK_INFLUX_URL=http://datenkrake.local:8086
DK_INFLUX_TOKEN=...
DK_INFLUX_ORG=datenkrake
DK_INFLUX_BUCKET=telemetrie

REPORT_USE_LLM=false
REPORT_LLM_URL=http://localhost:1234
REPORT_LLM_MODEL=local-model
REPORT_LLM_API_KEY=...
REPORT_LLM_TIMEOUT=30
```

## Prozesse und Reihenfolge

| # | Befehl | Rolle | Port |
| --- | --- | --- | --- |
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

Parallel dazu unverändert: **MariaDB → PHP-Dashboards** (`../Raspberry/web/audiodaten.php` und `../Raspberry/web/plcdaten.php`) und **MariaDB → MCP-Server → Claude Desktop**.

## Leitstand-Dashboard

`../Raspberry/web/index.html` liegt zusammen mit den beiden
Datenübersichten im Webroot. Der Dockerfile kopiert die Seiten sowie die
getrennt organisierten APIs in denselben `/var/www/html/`-Ordner.
Erreichbar unter `http://datenkrake.local/index.html`, verlinkt von beiden Übersichten aus.

Sie zeigt Agent-/Instrument-Cards, das Architektur-Diagramm, einen
LLM-Chat (LM Studio) sowie eine A2A-Konsole. Erreichbar unter
`http://datenkrake.local/index.html`, verlinkt von beiden Übersichten aus.

Live-Abrufe der Agent-Cards funktionieren nur, wenn die Agenten CORS für
den Browser-Ursprung erlauben (Standard-FastAPI/Starlette tut das nicht
automatisch) – siehe Hinweis im Dashboard selbst.

## Netzwerkannahme (aktuell)

- Raspberry Pi 5 per `eth0` im Anlagen-Netz `192.168.36.0/24`.
- Raspberry Pi 5 per `wlan0` als Client in einem bestehenden DMZ-WLAN.
- Laptop und Arduino-Systeme befinden sich ebenfalls in diesem DMZ-WLAN.
- Der Pi stellt dabei **keinen eigenen Hotspot/Access Point** bereit.

## Wichtige Einschränkung: noch keine Stationszuordnung

Das aktuelle Schema kennt nur EIN überwachtes Objekt (ein Arduino UNO Q,
ein Mikrofon). Sobald mehrere Arduino UNO Q an verschiedenen Stationen
betrieben werden, braucht `audio_spectrum` eine zusätzliche Spalte (z. B.
`station`), die dann durch `shared/db_service.py`, `anomalie_poller/`,
`orchestrator_agent/monitor.py` und `wartungs_agent/` durchgereicht wird.

## Abgrenzung fürs Tafelbild

| | MCP | A2A | LAP |
| --- | --- | --- | --- |
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
