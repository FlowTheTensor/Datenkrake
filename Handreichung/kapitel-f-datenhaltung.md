# Kapitel F · Datenhaltung und -analyse

[← Übersicht](README.md)

## Worum es geht

Die Datenkrake speichert dieselben Messwerte in **zwei Datenbanken**. Die
**MariaDB** ist die vollständige Quelle mit allen Feldern, kompletten Spektren und
den Tabellen der Agenten. **InfluxDB**, der Operational Historian, ist auf
schnelle Zeitreihen optimiert, und Grafana zeichnet daraus Verläufe. Dieses
Prinzip heißt Polyglot Persistence. Für große Auswertungen gibt es zusätzlich
den Data Lake auf einem eigenen Rechner.

## Lernziele

Die Schülerinnen und Schüler können …

- relationale Datenbank und Zeitreihendatenbank nach Stärken und Einsatzzweck unterscheiden,
- den Aufbau der Tabelle `plc_telemetry` erklären (welcher Wert landet in welcher Spalte),
- einfache SQL-Abfragen mit `SELECT`, `WHERE`, `ORDER BY` und `LIMIT` formulieren,
- begründen, warum Daten doppelt gespeichert werden, und nennen, was das kostet.

## Voraussetzungen

Ausbaustufe 1 (MariaDB, InfluxDB, Grafana). Mit echten Daten ab Stufe 2 oder 3,
den Data Lake ab Stufe 5.

## Zeitbedarf und Ablauf

2 DS.

| Phase | Dauer | Inhalt |
| --- | --- | --- |
| Einstieg | 15 min | Kapitel F: Warum zwei Datenbanken? |
| MariaDB | 45 min | PLC- und Audio-Übersicht ansehen, Spalten erklären, erste SQL-Abfragen |
| InfluxDB/Grafana | 30 min | Verlauf eines Signals in Grafana, Vergleich mit derselben Abfrage in SQL |
| Vertiefung | 30 min | „Reise eines Messwerts“, Halt 6–7 |
| Sicherung | 15 min | Quiz Kapitel F |

## Aufgaben und Musterlösungen

### Lernpfad „Datenanalyst“, Schritt 4: Zwei Datenbanken für dieselben Werte

> Warum speichert die Datenkrake in MariaDB und InfluxDB? Nennt für jede eine Aufgabe, für die sie besser geeignet ist.

**Musterlösung:**

| | MariaDB (relational) | InfluxDB (Zeitreihen) |
| --- | --- | --- |
| Stärke | vollständige Datensätze, beliebige Abfragen und Verknüpfungen, auch große Felder | sehr schnelle Abfragen über Zeiträume, Mittelwerte pro Minute oder Stunde |
| Bei der Datenkrake | komplette Spektren (641 Werte) für das Training, Tabellen der Agenten (`audio_anomalien`), Quelle für Zwilling und MCP | Verläufe in Grafana, Kennwerte (Frequenz, Pegel) für den Anomalie-Poller |
| Beispielaufgabe | „Gib mir alle schlecht gelabelten Messungen mit Spektrum“ | „Zeig den Pegelverlauf der letzten 24 Stunden“ |

**Preis der doppelten Speicherung:** mehr Speicherplatz, und beide Datenbanken
müssen gefüllt werden (Subscriber und Historian-Bridge). Fällt eine der beiden
Brücken aus, laufen die Datenbanken auseinander.

### Lernpfad „Automatisierer“, Schritt 6: Der Wert ist angekommen

> Sucht in der PLC-Übersicht die letzten Werte eurer Station. Passen sie zu dem, was ihr im Zwilling gesehen habt?

**Erwartung:** Die Schüler finden Zeilen ihrer Station (Spalte `station`, z. B.
`abf_llen`) und erkennen die Zuordnung: Boolesche Signale stehen in `wert_bool`
(0/1), Zahlen in `wert_num`. Die Spalte `quelle` unterscheidet `produktion` und
`team`.

Als SQL-Abfrage, z. B. im MCP-Server oder in einem Datenbank-Werkzeug:

```sql
SELECT ts, tag, wert_bool, wert_num, quelle
FROM plc_telemetry
WHERE station = 'abf_llen'
ORDER BY ts DESC
LIMIT 20;
```

**Zur Frage „Passt es zum Zwilling?“:** Ja, denn der Zwilling liest genau diese
Tabelle. Gute Antworten bemerken, dass zwischen zwei Zeilen desselben Tags oft
Sekunden oder Minuten liegen, weil nur Änderungen gespeichert werden.

## Weitere Aufgabenideen

- Wie viele Werte hat jede Station heute geliefert?
  `SELECT station, COUNT(*) FROM plc_telemetry WHERE ts >= CURDATE() GROUP BY station;`
- Vergleich Team und Produktion: Erfasst euer Stations-Tab gleich viele
  Bandsensor-Impulse wie der produktive Abgriff? Das ist auch eine gute
  Grundlage für ein Sprint Review.

## Typische Schwierigkeiten

- **Millisekunden fehlen.** `ts` speichert nur ganze Sekunden. Für die
  Reihenfolge innerhalb einer Sekunde muss man nach `id` sortieren.
- **„Zustand zu einem Zeitpunkt“.** Weil nur Änderungen gespeichert werden,
  steht der Zustand um 10:00 Uhr in der **letzten Zeile davor**, nicht in einer
  Zeile mit genau 10:00 Uhr.
- **`NULL` in `wert_num`.** Das ist richtig: Ein Wahrheitswert steht in `wert_bool`.
- **Grafana zeigt nichts an.** Den Zeitraum oben rechts prüfen, und ohne neue
  Daten bleibt das Diagramm leer.

## Bewertung

Woran man Verständnis erkennt:

- Stufe 2: Die Spalten der Tabelle werden richtig gedeutet.
- Stufe 3: Eine eigene SQL-Abfrage liefert die gewünschten Werte.
- Stufe 4: Die Wahl der Datenbank wird für eine neue Aufgabe begründet, und der Preis der Doppelspeicherung wird benannt.

## Material im Repo

- [`Raspberry/mariadb/init/`](../Raspberry/mariadb/init): Tabellenschema
- [`Raspberry/subscriber/`](../Raspberry/subscriber) und [`Raspberry/historian_bridge/`](../Raspberry/historian_bridge): die beiden Brücken
- [`Raspberry/historian/README.md`](../Raspberry/historian/README.md): InfluxDB
- [`DataLake/`](../DataLake): Lakehouse mit Notebook
- „Reise eines Messwerts“, Halte 6 und 7
- Quiz Kapitel F auf der Hauptseite
