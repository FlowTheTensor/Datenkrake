# Kapitel B · Theoretischer Unterbau: CRISP-DM

[← Übersicht](README.md)

## Worum es geht

CRISP-DM (Cross-Industry Standard Process for Data Mining) ist das
Vorgehensmodell hinter dem ganzen Projekt: sechs Phasen, die als **Kreislauf**
durchlaufen werden. Die Datenkrake macht das Modell greifbar, weil jede Phase
einem laufenden Teil des Systems entspricht.

## Lernziele

Die Schülerinnen und Schüler können …

- die sechs Phasen von CRISP-DM nennen und in die richtige Reihenfolge bringen,
- jeder Phase einen konkreten Schritt der Datenkrake zuordnen,
- begründen, warum CRISP-DM ein Kreislauf und keine Einbahnstraße ist,
- für ein eigenes Datenprojekt eine Fragestellung (Business Understanding) formulieren.

## Voraussetzungen

Ausbaustufe 0, nur der Browser.

## Zeitbedarf und Ablauf

1 DS, gut als Einstieg vor den Kapiteln C–H und als Rückblick am Ende.

| Phase | Dauer | Inhalt |
| --- | --- | --- |
| Einstieg | 10 min | Frage an die Klasse: „Woran merkt ein Instandhalter, dass mit einer Maschine etwas nicht stimmt?“ |
| Erarbeitung | 35 min | Kapitel B lesen, Phasen der Datenkrake zuordnen (Aufgabe unten) |
| Sicherung | 25 min | Kreislauf an der Tafel, Rückwege einzeichnen |
| Transfer | 20 min | eigenes Datenprojekt skizzieren (z. B. Energieverbrauch der Werkstatt) |

## Aufgaben und Musterlösungen

### Lernpfad „Erster Überblick“, Schritt 1: Warum gibt es die Datenkrake?

> Formuliert in einem Satz, welches Problem die Datenkrake lösen soll.

**Musterlösung:** Die Datenkrake soll Auffälligkeiten an der Modellanlage, etwa
ein ungewöhnliches Geräusch oder ein gestörter Ablauf, **früh und automatisch
erkennen**, damit gewartet werden kann, bevor etwas ausfällt.

Gute Antworten nennen das *Ziel* (früh erkennen, Ausfall vermeiden) und nicht
nur die *Technik* („Daten sammeln“).

### Lernpfad „Datenanalyst“, Schritt 1: Erst die Frage, dann die Daten

> Ordnet jeder CRISP-DM-Phase einen konkreten Schritt der Datenkrake zu. In welcher Phase steckt ihr gerade?

| Phase | Bei der Datenkrake |
| --- | --- |
| Business Understanding | Ziel festlegen: Anomalien an der Anlage früh erkennen, Wartung auslösen |
| Data Understanding | Audio-Spektren (`audio_spectrum`) und SPS-Signale (`plc_telemetry`) sichten, z. B. im Zwilling oder in Grafana |
| Data Preparation | Node-RED filtert unveränderte Werte heraus, setzt Zeitstempel und wandelt sie in JSON. Der Subscriber verteilt die Werte auf Spalten, die Historian-Bridge schreibt nur Kennwerte nach InfluxDB |
| Modeling | ML-Verfahren vergleichen, Isolation Forest oder LSTM trainieren |
| Evaluation | prüfen, ob der Anomalie-Detektor bei echten Messungen richtig liegt (falsche Alarme, übersehene Fälle) |
| Deployment | Anomalie-Poller läuft dauerhaft, der Orchestrator-Agent löst über den Wartungs-Agenten eine Reaktion aus |

„In welcher Phase steckt ihr?“ hat keine feste Lösung. Erwartet wird eine
begründete Einordnung. Bei der Arbeit an Node-RED-Flows ist das meist Data
Understanding oder Data Preparation.

## Typische Schwierigkeiten

- **CRISP-DM als Einbahnstraße.** Das Modell wird als lineare Abfolge gelernt.
  Gegenbeispiel aus dem Projekt: Bei der Fehlersuche zu verlorenen Sensorimpulsen
  (Data Understanding) zeigte sich, dass die SPS selbst einen Zähler braucht.
  Damit ändert sich die Datenerhebung, ein Schritt zurück im Kreislauf.
- **Business Understanding wird übersprungen.** Die Schüler wollen gleich ein
  Modell bauen. Immer zuerst die Frage stellen: „Was soll am Ende besser sein?“
- **Data Preparation wird unterschätzt.** In der Praxis steckt hier der größte
  Teil der Arbeit. Die Stolperstellen auf der Seite „Reise eines Messwerts“
  zeigen das gut.

## Bewertung

Woran man Verständnis erkennt:

- Stufe 2: Die Phasen werden in der richtigen Reihenfolge genannt.
- Stufe 3: Zu jeder Phase gibt es ein passendes Beispiel aus der Datenkrake.
- Stufe 4: Es wird erklärt, wann und warum man im Kreislauf zurückspringt, belegt mit einem Beispiel.

## Material im Repo

- [`Images/crisp-dm.svg`](../Images/crisp-dm.svg): Grafik des Kreislaufs
- Abschnitt „Zugrunde liegendes Vorgehensmodell“ im [Haupt-README](../README.md#zugrunde-liegendes-vorgehensmodell-crisp-dm)
- Quiz Kapitel B auf der Hauptseite
