# Architektur-Komponenten & Kommunikationsprotokolle

Übersicht aller Bausteine aus dem Architekturdiagramm (`index.html`), gegliedert nach den drei Zonen **Datenerhebung**, **Verarbeiten + Bereitstellen** (Datenkrake, Raspberry Pi 5) und **Analyse**.

---

## 1. Datenerhebung

| Komponente | Beschreibung | Kommuniziert mit | Protokoll | Richtung |
|---|---|---|---|---|
| **Akustik-KI** (Arduino UNO Q) | Edge-Gerät, live | Mosquitto | MQTT | Akustik-KI → Mosquitto |
| **YOLO-System** (Arduino UNO Q) | Edge-Gerät, *geplant* | Mosquitto | MQTT (geplant) | YOLO-System → Mosquitto |
| **Modellanlage** | Physische Anlage, SPS-Prozesswerte, ausschließlich lesender Zugriff (keine Steuerung) | Node-RED | OPC-UA | Modellanlage → Node-RED |

---

## 2. Verarbeiten + Bereitstellen (Datenkrake · Raspberry Pi 5, Docker-Stack)

| Komponente | Beschreibung | Kommuniziert mit | Protokoll | Richtung |
|---|---|---|---|---|
| **Mosquitto** | MQTT-Broker | Akustik-KI, YOLO-System | MQTT | eingehend |
| | | Node-RED | MQTT | eingehend (Bridge publiziert Werte) |
| | | MariaDB | Subscriber (schreibt via SQL) | Mosquitto → MariaDB |
| **Node-RED** | Bridge zwischen SPS-Welt (OPC-UA) und IoT-Welt (MQTT) | Modellanlage | OPC-UA | eingehend (liest SPS-Tags) |
| | | Mosquitto | MQTT | ausgehend (publiziert gelesene Tags) |
| | | InfluxDB | Historian-Bridge (internes Schreiben) | Node-RED → InfluxDB |
| **InfluxDB** | Operational Historian, nur skalare Werte (kein FFT-Array) | Node-RED | Historian-Bridge | eingehend |
| | | Anomalie-Poller | Flux-Query (HTTP API) | ausgehend (liefert Zeitreihenanalysen) |
| **MariaDB** | Zentrale Datenquelle, vollständige Telemetrie + Trainingsdaten | Mosquitto | SQL (Subscriber-Insert) | eingehend |
| | | Anomalie-Poller | SQL | bidirektional |
| | | DB-Agent | SQL | bidirektional |
| | | Report-Agent | SQL | bidirektional |
| | | Data-Lake-Server | Batch Import | ausgehend (periodisch) |
| | | MCP-Server | SQL (Netzwerk) | ausgehend |
| **Anomalie-Poller** | Pollt offene Anomalien, wertet Zeitreihen aus | MariaDB | SQL | bidirektional |
| | | InfluxDB | Flux-Query (HTTP API) | eingehend (ruft Zeitreihenanalysen ab) |
| | | Orchestrator-Agent | Trigger (internes Event) | Anomalie-Poller → Orchestrator-Agent |
| **Orchestrator-Agent** | A2A-Server + -Client, delegiert Aufgaben | DB-Agent | A2A | Orchestrator → DB-Agent |
| | | Wartungs-Agent | A2A | Orchestrator → Wartungs-Agent |
| | | Report-Agent | A2A | Orchestrator → Report-Agent |
| **DB-Agent** | A2A-Server | MariaDB | SQL | bidirektional |
| **Wartungs-Agent** | A2A-Server, LAP-Instrument | Zusatzgerät (Diagnose) | LAP | Wartungs-Agent → Zusatzgerät *(nie Produktionssteuerung/Modellanlage!)* |
| **Report-Agent** | A2A-Server | MariaDB | SQL | bidirektional |
| | | Browser (Analyse-Zone) | HTTP | eingehend (Agenten-Konsole spricht Agent Card direkt an) |
| **Zusatzgerät (Diagnose)** | Physisches Diagnosegerät, kein Produktionssystem | Wartungs-Agent | LAP | eingehend, nur nach expliziter Sicherheitsbestätigung |
| **Webserver** | Liefert `index.html` (dieses Dashboard) aus | Browser (Analyse-Zone) | HTTP | eingehend |

---

## 3. Analyse

| Komponente | Beschreibung | Kommuniziert mit | Protokoll | Richtung |
|---|---|---|---|---|
| **Server/PC · Data-Lake** (MinIO, Nessie, Spark + Jupyter) | Separater, stärkerer Rechner (nicht der Pi) | MariaDB | Batch Import | eingehend, periodisch |
| **MCP-Server** (`mcpserver.py`) | Läuft lokal auf dem PC, stdio-Anbindung | MariaDB | SQL (Netzwerk) | eingehend |
| | | Claude Desktop | MCP | ausgehend |
| **Claude Desktop** | Fertige Chat-App mit MCP-Unterstützung, ein MCP-Client unter mehreren | MCP-Server | MCP | eingehend |
| **Browser** | HTTP-Client | Webserver | HTTP | ausgehend |
| | | Report-Agent | HTTP | ausgehend (Agenten-Konsole spricht Agent Card direkt an) |

---

## Protokoll-Legende

| Protokoll | Verwendungszweck | Beispiel-Verbindung |
|---|---|---|
| **MQTT** | Publish/Subscribe, IoT-Telemetrie | Akustik-KI → Mosquitto |
| **OPC-UA** | Klassischer Industriestandard für Maschinenkommunikation (SPS) | Modellanlage → Node-RED |
| **SQL** | Datenbankzugriff (lesend/schreibend) | DB-Agent ↔ MariaDB |
| **A2A** | Agent-zu-Agent-Kommunikation (horizontale Kante) | Orchestrator-Agent → DB-Agent |
| **MCP** | Sprachmodell-zu-Werkzeug-Kommunikation (vertikale Kante) | MCP-Server → Claude Desktop |
| **LAP** | Agent-zu-physischem-Gerät (nach Sicherheitsbestätigung) | Wartungs-Agent → Zusatzgerät |
| **HTTP** | Web-Zugriff auf das Dashboard | Browser → Webserver |
| **Flux-Query (HTTP API)** | Zeitreihen-Abfrage gegen InfluxDB | Anomalie-Poller → InfluxDB |
| **Batch Import** | Periodische Massenübertragung in den Data-Lake | MariaDB → Data-Lake-Server |

## Begriffsklärung: Harness ist keine eigene Komponente

"Harness" taucht bewusst in keiner der Tabellen oben als eigenständiger
Baustein auf. Ein Harness ist die Tool-Aufruf-Schleife (LLM aufrufen →
bei Tool-Aufruf das Tool ausführen → Ergebnis zurückgeben → wiederholen,
bis das Modell fertig ist) plus ein Gedächtnis für den bisherigen
Verlauf – also eine Eigenschaft, die jeder Agent hier (Orchestrator-,
DB-, Wartungs-, Report-Agent) selbst mitbringt, kein zusätzlicher
Knoten im Diagramm. Ein Agent = Harness (Loop) + LLM + Tools + Memory.
