<img align="right" src="../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

hier ein Überblick über die typischen Bausteine, aus denen moderne LLM-Agenten heute bestehen:

1. LLM-Anbindung (das "Gehirn")
Der Agent ruft ein Sprachmodell über eine API auf (z. B. Anthropic, OpenAI, lokal via Ollama/vLLM). Wichtig dabei:

Function/Tool Calling: das Modell gibt strukturierte Aufrufe zurück (JSON), die der Agent-Code dann ausführt
System Prompt: definiert Rolle, Werkzeuge, Verhaltensregeln
Structured Outputs: erzwungene JSON-Schemas für zuverlässige Weiterverarbeitung

2. Tools/Werkzeuge
Der Agent bekommt Zugriff auf externe Fähigkeiten: Websuche, Code-Ausführung (Sandbox), Dateisystem, APIs (Kalender, E-Mail, Datenbanken), andere Services via MCP (Model Context Protocol) – das hat sich als eine Art USB-Standard für Tool-Integration etabliert.

3. Loop/Steuerung
Das Herzstück ist eine Schleife, meist nach dem ReAct-Muster (Reasoning + Acting):

Modell denkt nach / plant nächsten Schritt
Modell ruft ein Tool auf
Ergebnis wird zurück in den Kontext gegeben
Wiederholen, bis Ziel erreicht oder Abbruchkriterium

Varianten: Plan-and-Execute (erst kompletten Plan erstellen, dann abarbeiten), Reflection/Self-Critique (Agent bewertet eigene Zwischenergebnisse), Multi-Agent-Orchestrierung (mehrere spezialisierte Agenten, ein Orchestrator delegiert).

4. Memory
Meist zweigeteilt:

Kurzzeit/Working Memory: der Konversationskontext selbst (begrenzt durch Context Window)
Langzeit-Memory: externe Speicherung, oft via Vektordatenbank (Embeddings + semantische Suche), manchmal auch strukturiert als Key-Value-Store oder Graph. Wird genutzt, um über Sessions hinweg Fakten, Präferenzen oder frühere Interaktionen abrufbar zu machen (Retrieval-Augmented Generation, RAG)

5. State & Checkpoints
Bei längeren oder kritischen Workflows wird der Agentenzustand persistiert:

Checkpoints erlauben, nach einem Absturz oder bei Human-in-the-loop-Unterbrechungen genau dort weiterzumachen, wo man war
Ermöglicht auch "Time Travel" (zu einem früheren Zustand zurückspringen) und parallele Exploration verschiedener Pfade
Frameworks wie LangGraph modellieren das explizit als Graph mit persistenten States

6. Orchestrierungs-Frameworks
LangGraph, CrewAI, AutoGen, Semantic Kernel, oder selbstgebaute State-Machines – sie strukturieren Loop, Memory und Tool-Aufrufe in eine handhabbare Architektur statt alles in einem großen Prompt zu bündeln.

7. Guardrails & Kontrolle

Human-in-the-loop-Freigaben vor kritischen Aktionen (z. B. E-Mail senden, Geld überweisen)
Kosten-/Zeit-/Iterationslimits gegen Endlosschleifen
Output-Validierung, Content-Filter

8. Observability
Tracing-Tools (z. B. LangSmith, Langfuse) protokollieren jeden Schritt – welches Tool wann mit welchen Parametern aufgerufen wurde, was das Modell "gedacht" hat – wichtig für Debugging, da Agentenverhalten sonst schwer nachvollziehbar ist.


# Agentensystem (MCP, A2A, LAP)

Setzt auf dem bestehenden IoT-Stack (`../Raspberry/`) auf und ergänzt ihn
um drei Agentenprotokolle. Keine bestehende Komponente (Arduino UNO Q,
Mosquitto, MariaDB, Subscriber, Web-Dashboard) wird verändert oder ersetzt.

- **MCP** – `../MCPLokalClaudDesktop/mcpserver.py` (erweitert, siehe dortiger Commit) für Claude Desktop
- **A2A** – `db_agent/`, `orchestrator_agent/`, `report_agent/`
- **LAP** – `lap_common/`, `wartungs_agent/`

### Begriffsklärung: Was ist ein "Harness"?

"Harness" ist hier bewusst **keine eigene Komponente** neben MCP, A2A und
LAP, sondern eine Eigenschaft, die jeder der obigen Agenten (Orchestrator-,
DB-, Wartungs-, Report-Agent) bereits mitbringt: ein Harness ist die
Schleife, die aus einem rohen Sprachmodell überhaupt erst einen Agenten
macht – Tools/Ressourcen anbieten, das LLM aufrufen, bei einem
Tool-Aufruf das Tool ausführen und das Ergebnis zurückgeben, das Ganze
wiederholen, bis eine Antwort ohne weiteren Tool-Aufruf kommt. Dazu
kommt ein Gedächtnis (der bisherige Konversations-/Aufgabenverlauf), das
zwischen den Schleifendurchläufen erhalten bleibt. Ein Agent besteht also
immer aus **Harness (Tool-Aufruf-Schleife) + LLM + Tools + Memory** –
nicht aus einem Harness *und* separat noch einem Agenten. Orchestrator-,
DB- und Report-Agent können inzwischen optional ein lokales LLM (LM
Studio) für ihren jeweiligen Sprach-/Auswahlanteil nutzen (siehe
"LLM-Anbindung" unten); der Wartungs-Agent bleibt bei seiner
Sicherheitsentscheidung (Safety-Fence) bewusst regelbasiert – dazu mehr
im selben Abschnitt.

## LLM-Anbindung (LM Studio)

Alle vier Agenten sprechen bei Bedarf dasselbe OpenAI-kompatible
Chat-Completions-API an (`shared/llm_client.py`), standardmäßig ein
lokales LM Studio (`LLM_BASE_URL`, Standard `http://localhost:1234`).
Jeder Agent hat einen eigenen An/Aus-Schalter und kann optional die
Defaults überschreiben (`.env.example` zeigt alle Variablen):

| Agent | Schalter | Wofür das LLM genutzt wird | Fallback ohne LLM |
| --- | --- | --- | --- |
| DB-Agent | `DB_AGENT_USE_LLM` | wählt per Tool-Calling zwischen den Werkzeugen `offene_anomalien`/`statistik` | Keyword-Abgleich (`anomalie`/`wartung`/`stats`) |
| Orchestrator-Agent | `ORCHESTRATOR_USE_LLM` | formuliert die Statusantwort auf `wartungsstatus_melden` in Sprache | fixer Text `"N offene Anomalie(n) in Bearbeitung."` |
| Report-Agent | `REPORT_USE_LLM` | formuliert die Produktionsmeldung aus dem Orchestrator-Ereignis | festes Template mit Zeitstempel |
| Wartungs-Agent | `WARTUNGS_AGENT_USE_LLM` | kommentiert das Messergebnis (`kommentar`-Feld) in einem Satz | kein Kommentar-Feld in der Antwort |

**Sicherheitsgrundsatz:** Das LLM formuliert oder wählt hier nur zwischen
bereits vorhandenen, harmlosen Lese-Werkzeugen bzw. Text – es trifft nie
die Safety-Fence-Entscheidung des Wartungs-Agent (ob eine gefährliche
Aktion wie `schmierzyklus` bestätigt werden muss). Diese Entscheidung
bleibt vollständig in `lap_common/base.py`/`wartungs_agent/instrument.py`
fest im Code, unabhängig davon, ob `WARTUNGS_AGENT_USE_LLM` gesetzt ist.
Jeder LLM-Aufruf ist zudem in ein `try/except` mit Fallback auf die
bisherige, deterministische Logik eingebettet – ohne laufendes LM Studio
funktioniert also weiterhin alles wie zuvor.

## LangGraph: interne Abläufe & Visualisierung

Orchestrator-, DB- und Report-Agent bilden ihre interne Entscheidungslogik
jetzt jeweils als kompilierten `langgraph`-Graphen ab (`graph.py` im
jeweiligen Ordner) statt als lineare if/for-Ketten. Die A2A-Schnittstelle
nach außen (Agent Card, Skill) bleibt unverändert – intern ruft der
Executor bzw. die Überwachungsschleife nur noch `GRAPH.ainvoke(...)` auf.

| Agent | Graph zeigt |
| --- | --- |
| `orchestrator_agent/graph.py` | Warteschlange offener Anomalien → LAP-Wartung auslösen → abschließen → Report-Agent benachrichtigen (Schleife, bis die Warteschlange leer ist) |
| `db_agent/graph.py` | Anfrage verstehen (LLM-Werkzeugwahl oder Keyword-Fallback) → Werkzeug ausführen |
| `report_agent/graph.py` | LLM-Formulierung versuchen → bei Erfolg fertig, sonst Template-Fallback |

Jeder dieser drei Agenten liefert unter `GET /graph/mermaid` den
Mermaid-Quelltext seines Graphen aus (kein CORS-Header gesetzt, siehe
Hinweis zu den Agent-Cards weiter unten) – der Leitstand
(`../Raspberry/web/index.html`, Tab "Agenten-Graphen") ruft das live ab
und rendert es mit mermaid.js. Das ist bewusst dieselbe Technik wie im
didaktischen `langgraph-werkstatt/` (dort mit fiktiven Beispielknoten zum
Selberbauen) – dort können Schüler den Aufbau eines Graphen gefahrlos
üben, bevor sie die echten Graphen hier lesen oder erweitern.
Wartungs-Agent bleibt bewusst ohne eigenen Graphen: er ist kein A2A-
Agent mit mehrstufiger Entscheidungslogik, sondern ein LAP-Instrument mit
fester Aktionsausführung (siehe LLM-Anbindung oben).

## Vorausschauende Instandhaltung (`ml_training/`)

Zusätzlich zur festen Mittelwert/Standardabweichungs-Heuristik können
Schüler in `ml_training/` selbst zwei Modelle trainieren:

- **Isolation Forest** (`train_isolation_forest_akustik.py`) auf den
  echten `audio_spectrum`-Daten aus der MariaDB (Merkmale `peak_freq`,
  `peak_db`) – Ersatz für `ANOMALIE_METHODE=isolation_forest` im
  `anomalie_poller`.
- **LSTM** (`train_lstm_durchlaufzeit.py`) auf Durchlaufzeiten/Zykluszeiten
  – aktuell **mit synthetischen Demodaten**, weil die reale
  OPC-UA-Anbindung dieser Werte in die MariaDB noch aussteht (siehe
  `todo.md`, "opc-ua overlay überarbeiten"). Sobald `raw_signals` befüllt
  wird, liest das Skript automatisch echte Werte statt der Demodaten.

Beide Skripte legen ihre trainierten Modelle unter `ml_training/models/`
ab (nicht versioniert, siehe `.gitignore`); `shared/predictive_models.py`
lädt sie zur Laufzeit und fällt ohne trainiertes Modell automatisch auf
die bisherige Heuristik zurück. Details: [`ml_training/README.md`](ml_training/README.md).

## Was neu dazukommt

| Neu | Ersetzt/ergänzt |
| --- | --- |
| `../MCPLokalClaudDesktop/mcpserver.py` | **erweitert** (alle 5 bestehenden Tools unverändert) um 1 Tool, 2 Resources, 1 Prompt |
| `../Raspberry/mariadb/init/01-agentensystem.sql` | **ergänzt** `00-create-database.sql` um 2 Tabellen + 1 User |
| `../Raspberry/web/index.html` | **ergänzt** die getrennten Audio- und PLC-Datenübersichten um den Leitstand |
| `anomalie_poller/` | überbrückt die im Haupt-README unter "Nächste Schritte" genannten offenen Punkte "Echtzeit-Inferenz" / "Alarm-System" |
| `wartungs_agent/`, `lap_common/` | LAP-Instrument-Agent |
| `db_agent/`, `orchestrator_agent/`, `report_agent/` | A2A-Schicht, intern jeweils ein `graph.py` (LangGraph) |
| `shared/` | gemeinsame DB-Zugriffsschicht + `llm_client.py` (LM Studio) + `predictive_models.py` |
| `ml_training/` | Trainingsskripte für Isolation Forest (Akustik) und LSTM (Durchlaufzeit) |

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
   - `ANOMALIE_METHODE=zscore` (Standard) nutzt die feste Heuristik, `ANOMALIE_METHODE=isolation_forest` das selbst trainierte Modell aus `ml_training/`.
   - `<AGENT>_USE_LLM=true` (z. B. `REPORT_USE_LLM`, `DB_AGENT_USE_LLM`, `ORCHESTRATOR_USE_LLM`, `WARTUNGS_AGENT_USE_LLM`) aktiviert optional die LM-Studio-Anbindung des jeweiligen Agenten.
   - Ohne `_USE_LLM=true` bzw. ohne trainiertes ML-Modell nutzt jeder Agent automatisch die bisherige, offline-fähige feste Logik (Fallback).
3. Wichtig zur Architektur:
   - Erkennung kann aus Influx kommen, der Poller schreibt trotzdem in `audio_anomalien` (MariaDB).
   - Dadurch bleiben Orchestrator-, Wartungs- und Reporting-Kette unverändert kompatibel.
   - Ein Agent nutzt ein LLM nur, wenn sein `_USE_LLM`-Schalter auf `true` steht - siehe "LLM-Anbindung" oben.

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

- Safety-Fence-Bestätigung wird in der Demo automatisch erteilt (`orchestrator_agent/graph.py`) statt von einer Aufsichtsperson – in echt hier ansetzen.
- `pruefe_akustik_anomalie()` (in `mcpserver.py` und `shared/db_service.py`) ist eine einfache Mittelwert/Standardabweichungs-Heuristik – optional ersetzbar durch das selbst trainierte Isolation-Forest-Modell aus `ml_training/` (`ANOMALIE_METHODE=isolation_forest`).
- Der `orchestrator_agent` liest den Anomalie-Status aktuell direkt über `shared/db_service.py` statt über einen A2A-Hop zum `db_agent` (spart einen Netzwerk-Sprung in der Demo). Der `db_agent` bleibt trotzdem ein regulärer A2A-Server für andere Agenten oder Menschen, die ihn ansprechen wollen.
- Die LSTM-Durchlaufzeitvorhersage (`ml_training/train_lstm_durchlaufzeit.py`) trainiert aktuell auf synthetischen Demodaten, weil die reale OPC-UA-Anbindung der Zykluszeiten in die MariaDB noch aussteht.
- `/graph/mermaid` setzt keinen CORS-Header – für den Leitstand-Tab "Agenten-Graphen" gilt dieselbe Einschränkung wie für die Agent-Cards (siehe oben).
