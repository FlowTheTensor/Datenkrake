# Kapitel H · Agentensysteme & KI-Integration

[← Übersicht](README.md)

## Worum es geht

Drei Protokolle verbinden unterschiedliche Dinge, und diese Unterscheidung ist
der Kern des Kapitels:

- **MCP** verbindet ein Sprachmodell mit Werkzeugen und Daten. So bekommt Claude
  Desktop lesenden Zugriff auf die MariaDB.
- **A2A** verbindet eigenständige Agenten miteinander. Der Orchestrator
  delegiert an DB- und Report-Agent.
- **LAP** verbindet einen Agenten mit einem physischen Gerät. Der Wartungs-Agent
  steuert sein Diagnosegerät erst nach einer ausdrücklichen Bestätigung.

Jeder Agent ist dabei sein eigener **Harness**: die Schleife aus LLM-Aufruf,
Werkzeug-Ausführung und Gedächtnis. Den Ablauf beschreiben die Agenten als
LangGraph-Graph.

## Lernziele

Die Schülerinnen und Schüler können …

- MCP, A2A und LAP nach dem unterscheiden, was sie verbinden,
- erklären, was einen Agenten von einem einfachen Chatbot unterscheidet (Harness: Werkzeuge, Schleife, Gedächtnis),
- die Kette von der Anomalie bis zum Bericht beschreiben,
- begründen, warum physische Aktionen eine menschliche Bestätigung brauchen,
- einen einfachen Agentenablauf als Graph modellieren (LangGraph-Werkstatt).

## Voraussetzungen

Ausbaustufe 0 für Theorie und LangGraph-Werkstatt (Python auf den
Schülerrechnern). Die echten Agenten ab Ausbaustufe 4, sinnvoll zusammen mit
Stufe 2, damit es Anomalien gibt.

## Zeitbedarf und Ablauf

2–3 DS.

| Phase | Dauer | Inhalt |
| --- | --- | --- |
| Einstieg | 20 min | Architektur: Wer redet mit wem? (siehe [Kapitel C](kapitel-c-infrastruktur.md)) |
| Protokolle | 40 min | MCP-Werkzeuge, A2A und LAP am Beispiel der Datenkrake |
| Werkstatt | 60–90 min | LangGraph-Werkstatt: Ablauf verändern, Graph erklären |
| Live | 30 min | Agenten-Konsole (nur mit Stufe 4): Orchestrator befragen, Graph ansehen |
| Diskussion | 20 min | Sicherheit und Verantwortung bei KI mit Zugriff auf Geräte |
| Sicherung | 15 min | Quiz Kapitel H |

## Aufgaben und Musterlösungen

### Lernpfad „Erster Überblick“, Schritt 5: Wo kommt die KI ins Spiel?

> Was ist der Unterschied zwischen MCP, A2A und LAP? Je ein Satz.

**Musterlösung:**

- **MCP:** Ein Sprachmodell bekommt Werkzeuge und Daten, etwa Datenbankabfragen.
- **A2A:** Zwei eigenständige Agenten sprechen miteinander und geben sich Aufgaben weiter.
- **LAP:** Ein Agent steuert ein echtes Gerät, aber nur nach Reservierung und Sicherheitsbestätigung.

### Lernpfad „KI-Agenten-Bauer“, Schritt 2: Der Auslöser

> Was muss passieren, damit die Agenten überhaupt aktiv werden?

**Musterlösung:** eine Kette aus fünf Schritten.

1. Der Arduino nimmt auf (Aufnahme gestartet) und sendet einmal pro Sekunde eine Messung.
2. Die Messung landet in der Datenbank.
3. Der **Anomalie-Poller** prüft alle 15 Sekunden und findet eine auffällige Messung.
4. Er schreibt einen Eintrag in die Tabelle `audio_anomalien`.
5. Der **Orchestrator** schaut alle 20 Sekunden nach offenen Anomalien und beginnt mit der Bearbeitung.

**Stufe 4:** Die Agenten reagieren nicht auf das Geräusch selbst, sondern auf
einen **Datenbankeintrag**. Der Poller ist eine Übergangslösung und könnte
später durch Ereignisse ersetzt werden, die der Arduino direkt per MQTT sendet.

### Lernpfad „KI-Agenten-Bauer“, Schritt 3: MCP, Werkzeuge für ein Sprachmodell

> Welche Frage könnte ein Sprachmodell mit welchem Werkzeug beantworten? Drei Beispiele.

**Mögliche Lösungen:**

| Frage an das Sprachmodell | Werkzeug |
| --- | --- |
| „Wie sahen die letzten zehn Messungen aus?“ | `get_recent(10)` |
| „Gibt es mehr gute oder mehr schlechte Messungen, und wie unterscheiden sie sich?“ | `get_stats()` |
| „Ist gerade etwas auffällig?“ | `pruefe_akustik_anomalie(fenster)` |
| „Zeig mir das komplette Spektrum von Messung 4711.“ | `get_spectrum(4711)` |
| „Welche Spalten hat die Tabelle?“ | `get_table_info()` |
| „Wie viele Messungen gab es gestern?“ | `query(sql)` mit einer selbst formulierten SELECT-Abfrage |

Außerdem gibt es die **Resources** `schema://overview` und `anomalien://offen`
sowie den **Prompt** `anomalie_analysieren()`. **Stufe 4:** Das Modell
entscheidet selbst, welches Werkzeug es aufruft. Die Werkzeugbeschreibung ist
deshalb genauso wichtig wie das Werkzeug.

### Lernpfad „KI-Agenten-Bauer“, Schritt 4: Sicherheit zuerst

> Warum verlangt der Wartungs-Agent vor jeder Aktion eine Bestätigung, und warum darf er nie an die Produktionssteuerung?

**Musterlösung:**

- **Physische Aktionen lassen sich nicht rückgängig machen.** Eine falsche
  Antwort im Chat ist ärgerlich, ein falsch ausgelöster Schmierzyklus oder eine
  bewegte Achse kann Schaden anrichten.
- **Sprachmodelle können sich irren.** Sie können eine Lage falsch einschätzen
  oder durch manipulierte Eingaben getäuscht werden. Ein Mensch prüft deshalb
  vor jeder Aktion (Human in the loop).
- **Verantwortung bleibt beim Menschen.** Wer bestätigt, übernimmt die Verantwortung.
- **Trennung von der Produktion.** Der Wartungs-Agent hat nur ein eigenes
  Diagnosegerät. Die Produktionssteuerung ist für ihn gar nicht erreichbar.
  Selbst bei einem Fehler kann er die Anlage nicht beeinflussen. Auch der
  Datenzugriff über MCP ist nur lesend.

Diese Sicherheitsentscheidung ist **bewusst regelbasiert** und nicht dem LLM
überlassen.

### Lernpfad „KI-Agenten-Bauer“, Schritt 5: Selbst einen Ablauf bauen

> Verändert in der LangGraph-Werkstatt einen Agentenablauf, lasst euch den Graphen anzeigen und erklärt ihn eurem Nachbarteam.

**Erwartung:** Es gibt keine feste Lösung. Gute Ergebnisse:

- verändern den Ablauf sinnvoll, etwa mit einem zusätzlichen Prüfschritt, einer
  neuen Verzweigung oder einer menschlichen Freigabe über die
  `interrupt()`-Zusatzaufgabe,
- zeigen den Graphen und erklären jeden Knoten und jede Bedingung,
- können vorhersagen, welchen Weg ein bestimmtes Szenario nimmt, und prüfen das
  im simulierten Durchlauf.

### Lernpfad „KI-Agenten-Bauer“, Schritt 6: Die echten Agenten fragen

> Sprecht in der Agenten-Konsole mit dem Orchestrator. Vergleicht seinen Graphen mit eurem aus der Werkstatt.

**Der Graph des Orchestrators:**

```text
START → anomalien_lesen → (offene Anomalien?)
          nein → ENDE
          ja   → naechste_anomalie → wartung_ausloesen → anomalie_abschliessen
                 → bericht_melden → (weitere offen?) ja → naechste_anomalie
                                                     nein → ENDE
```

Erwartete Beobachtungen: eine **Schleife**, die alle offenen Anomalien
nacheinander abarbeitet, eine **Verzweigung** am Anfang und nach jedem Bericht.
In `wartung_ausloesen` fordert der Orchestrator per LAP einen Schmierzyklus an,
in `bericht_melden` geht der Bericht per A2A an den Report-Agenten.

## Typische Schwierigkeiten

- **MCP und A2A verwechseln.** Merkhilfe: MCP ist „Modell ↔ Werkzeug“, A2A ist
  „Agent ↔ Agent“.
- **„Die KI macht das selbst.“** Vieles ist feste Logik: der Poller, die
  Sicherheitsabfrage, der Graph. Das Sprachmodell formuliert und wählt
  Werkzeuge, wenn es eingeschaltet ist. Ohne LLM laufen die Agenten mit
  festen Regeln weiter.
- **Agenten-Konsole zeigt „demo“ oder einen Fehler.** Die Agenten laufen nicht,
  oder der Browser darf sie nicht erreichen (CORS). Das betrifft nur die Live-Phase.
- **Python auf Schülergeräten.** Für die Werkstatt vorher klären, ob Python
  installiert oder freigegeben ist.

## Bewertung

Woran man Verständnis erkennt:

- Stufe 2: Die drei Protokolle werden richtig zugeordnet.
- Stufe 3: Die Kette von der Anomalie bis zum Bericht wird vollständig beschrieben.
- Stufe 4: Sicherheitsentscheidungen werden begründet (warum regelbasiert, warum getrennt), und der eigene Graph wird mit dem echten verglichen.

## Material im Repo

- [`Agentensystem/`](../Agentensystem): alle Agenten, Einrichtung und Start
- [`Agentensystem/langgraph-werkstatt/`](../Agentensystem/langgraph-werkstatt): Werkstatt für Schülerlaptops
- [`MCPLokalClaudeDesktop/`](../MCPLokalClaudeDesktop): MCP-Server für Claude Desktop
- „Reise einer Akustikmessung“, Halte 5 und 6
- Quiz Kapitel H auf der Hauptseite
