# Orchestrator-Agent

Der Orchestrator ueberwacht neue Anomalien und delegiert Wartungsaktionen sowie Report-Aufgaben an die passenden Agenten.

## Start

```text
python -m orchestrator_agent
```

Der A2A-Server laeuft auf Port `9200` und startet zusaetzlich die Ueberwachungsschleife. Datenbank-, Report- und Wartungs-Agent sollten vorher gestartet werden.