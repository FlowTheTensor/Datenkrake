<img align="right" src="../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# Lokaler MCP-Server fuer Claude Desktop

Dieser Ordner enthaelt einen lokalen [MCP](https://modelcontextprotocol.io/)-Server fuer Claude Desktop. Der Server verbindet Claude mit der MariaDB der Datenkrake und stellt Telemetrie sowie Informationen aus dem Agentensystem lesend bereit.

## Funktionen

Der Server bietet unter anderem:

- aktuelle Eintraege aus `audio_spectrum`
- Statistiken zu Audio-Spektren
- einzelne Datensaetze inklusive FFT-Spektrum
- begrenzte `SELECT`-, `SHOW`- und `DESCRIBE`-Abfragen
- Informationen zum Datenbankschema
- eine statistische Pruefung auf akustische Anomalien
- eine Liste offener Anomalien
- einen Prompt zur Analyse aktueller Anomalien

Der Server verwendet den Datenbankbenutzer `mcp_read` und ist fuer lesenden Zugriff vorgesehen. Er laeuft ueber `stdio`, damit Claude Desktop direkt mit ihm kommunizieren kann.

## Voraussetzungen

- Python 3
- erreichbare Datenbank unter `datenkrake.local:3306`
- Datenbank `telemetry` mit den benoetigten Tabellen

Abhaengigkeiten werden aus `requirements.txt` installiert:

```text
python -m pip install -r requirements.txt
```

## Einbindung in Claude Desktop

In der Claude-Desktop-Konfiguration wird der Server als lokaler MCP-Prozess eingetragen. Beispiel fuer Windows:

```json
{
  "mcpServers": {
    "datenkrake": {
      "command": "python",
      "args": [
        "C:/Pfad/zum/Projekt/MCPLokalClaudeDesktop/mcpserver.py"
      ]
    }
  }
}
```

Den Beispielpfad durch den lokalen absoluten Pfad zum Projekt ersetzen und Claude Desktop anschliessend neu starten.

## Manueller Start

```text
python mcpserver.py
```

Der Prozess bleibt im Vordergrund und wartet auf MCP-Nachrichten ueber stdin/stdout. Fuer Claude Desktop wird er normalerweise automatisch durch die Konfiguration gestartet.