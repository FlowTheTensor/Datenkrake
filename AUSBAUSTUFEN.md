<img align="right" src="Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# Ausbaustufen: Was brauche ich mindestens?

Die Datenkrake ist an einer Modellanlage mit zehn SPS-Stationen entstanden,
für den Unterricht braucht man die aber nicht. Das Projekt ist in Stufen
aufgebaut, die aufeinander aufsetzen. Jede Stufe ist für sich im Unterricht
nutzbar, man kann also klein anfangen und später erweitern.

| Stufe | Was dazukommt | Einrichtung | Damit möglich |
| --- | --- | --- | --- |
| **0 · Nur Browser** | nichts, nur Internetzugang | keine | Kapitel lesen, Quiz, Glossar, Zwilling-Demo, LangGraph-Werkstatt |
| **1 · Raspberry Pi** | Raspberry Pi 4/5 mit Docker-Stack | ca. 1 Stunde | eigener Leitstand, MQTT, Node-RED, Datenbanken, Grafana, Forgejo für agiles Arbeiten |
| **2 · Akustik** | Arduino UNO Q, USB-Mikrofon/Webcam, PD-Dockingstation | ca. 1–2 Stunden | echte Messdaten, Machine Learning, Anomalie-Erkennung |
| **3 · Echte SPS** | eine oder mehrere SPSen mit OPC-UA-Server | je nach Anlage | Industrie-4.0-Datenerhebung, Stationsteams, digitaler Zwilling mit eigenen Daten |
| **4 · Agenten** | PC mit Python, optional LM Studio oder Claude Desktop | ca. 1 Stunde | Agentensystem mit MCP, A2A und LAP |
| **5 · Data Lake** | zweiter, stärkerer Rechner mit Docker | ca. 1 Stunde | Lakehouse mit MinIO, Nessie, Spark/Jupyter |

Die Zeiten sind grobe Richtwerte für jemanden, der schon einmal mit der
Kommandozeile gearbeitet hat. Stufe 2 und Stufe 3 sind unabhängig voneinander,
man kann also auch mit der SPS anfangen und die Akustik weglassen.

Wie man die Kapitel dann im Unterricht umsetzt, mit Lernzielen, Ablauf und
Musterlösungen, steht in der [Handreichung](Handreichung/README.md).

## Welche Kapitel gehen ab welcher Stufe?

Der Leitstand gliedert das Projekt in die Kapitel A–H. „Lesen“ heißt: Erklärungen,
Diagramme und Quiz funktionieren. „Praktisch“ heißt: Die Schülerinnen und Schüler
arbeiten am laufenden System.

| Kapitel | Lesen ab | Praktisch ab |
| --- | --- | --- |
| A Agiles Arbeiten | 0 | 1 (Forgejo, Node-RED), mit Stationsteams ab 3 |
| B Theoretischer Unterbau (CRISP-DM) | 0 | durchgehend, sobald eigene Daten da sind (2 oder 3) |
| C Infrastruktur & Hardware | 0 | 1 |
| D Datenerhebung | 0 (Zwilling-Demo) | 2 (Akustik) bzw. 3 (SPS) |
| E Kommunikation & Industrie 4.0 | 0 | 1 (MQTT, Node-RED, OPC-UA-Demo-Server) |
| F Datenhaltung und -analyse | 0 | 1, mit echten Daten ab 2; Data Lake ab 5 |
| G Machine Learning | 0 | 1 (LSTM mit synthetischen Daten), 2 (Akustik) |
| H Agentensysteme | 0 (LangGraph-Werkstatt) | 4 |

---

## Stufe 0 · Nur Browser

**Braucht:** einen Browser. Für die LangGraph-Werkstatt zusätzlich Python 3.10
oder neuer auf den Schülerrechnern.

**Damit geht:**

- Der komplette **Leitstand** unter
  [flowthetensor.github.io/Datenkrake](https://flowthetensor.github.io/Datenkrake/)
  mit allen Kapiteln, Architekturdiagrammen, **Quiz** (zehn Fragen pro Kapitel)
  und **Glossar**.
- Der **digitale Zwilling**
  ([anlage-zwilling.html](https://flowthetensor.github.io/Datenkrake/anlage-zwilling.html))
  spielt eine aufgezeichnete Produktion der Modellanlage ab. Daran lässt sich
  zeigen, wie Sensorimpulse und Motorlauf zusammenhängen, ohne eine Anlage
  zu besitzen.
- Die **LangGraph-Werkstatt** läuft auf jedem Schülerlaptop. Dort modellieren
  die Schülerinnen und Schüler Agentenabläufe in Python und sehen sie als
  Diagramm. Sie arbeitet mit simulierten Agenten und braucht kein Datenkrake-Netz.
  Anleitung: [`Agentensystem/langgraph-werkstatt/README.md`](Agentensystem/langgraph-werkstatt/README.md).

**Geht noch nicht:** alles, was live ist: Agenten-Konsole, Links zu Node-RED,
Grafana und Forgejo, eigene Daten.

**Gut für:** einen ersten Eindruck, Vertretungsstunden, die Theorie zu CRISP-DM
und den Agentenprotokollen, Hausaufgaben mit Quiz.

---

## Stufe 1 · Raspberry Pi

**Braucht:**

- Raspberry Pi 4 oder 5 mit mindestens 4 GB RAM, Raspberry Pi OS **64-Bit**
- SD-Karte ab 16 GB; für Dauerbetrieb besser eine **SSD**, weil InfluxDB sehr
  häufig schreibt und SD-Karten dabei schnell verschleißen
- Netzwerk, in dem Schülerrechner den Pi erreichen
- einen USB-Stick (exFAT, Bezeichnung `DATENKRAKE`) für die Datensicherung,
  am besten zwei im Wechsel

**Einrichtung:** Rechnername `datenkrake` im Raspberry Pi Imager setzen, Repo
klonen, `sudo ./setup_iot_stack.sh` ausführen. Das Skript installiert Docker und
startet alle Dienste. Danach die „Ersten Schritte“ erledigen (Forgejo-Konten,
erste Sicherung). Schritt für Schritt im [Haupt-README](README.md#schnellstart-klonen-installieren-updaten).

**Damit geht:**

- Leitstand unter `http://datenkrake.local`, jetzt mit Live-Status
- **MQTT** (Mosquitto) zum Ausprobieren von Publish/Subscribe und Topics
- **Node-RED** mit dem mitgelieferten **OPC-UA-Demo-Server**. Der simuliert einen
  einzelnen Wert, eine schwankende Zykluszeit mit gelegentlichen Ausreißern.
  Damit lässt sich die Kette OPC-UA → Node-RED → MQTT → Datenbank komplett
  aufbauen, ohne dass eine SPS da ist
  ([`Raspberry/opcua_demo_server/README.md`](Raspberry/opcua_demo_server/README.md)).
- **MariaDB** und **InfluxDB** mit **Grafana** für SQL-Abfragen und Dashboards
- **Forgejo** mit Backlog, Kanban-Board und Schülerkonten. Damit funktioniert
  Kapitel A „Agiles Arbeiten“ vollständig: Jeder Deploy in Node-RED wird
  automatisch als Commit gesichert.
- Das **LSTM-Training** (Kapitel G) erzeugt bei fehlenden Anlagendaten
  selbst einen gekennzeichneten synthetischen Datensatz
  ([`Agentensystem/ml_training/README.md`](Agentensystem/ml_training/README.md)).

**Grenzen:** Ohne Akustik oder SPS kommen nur die Werte des Demo-Servers in die
Datenbank. Der digitale Zwilling auf dem Pi spielt deshalb die mitgelieferte
Aufzeichnung unserer Modellanlage ab, bis die eigene Datenbank Produktionen enthält.

---

## Stufe 2 · Akustik mit dem Arduino UNO Q

**Braucht:**

- Arduino UNO Q
- USB-Mikrofon oder Webcam mit Mikrofon
- USB-C-Dockingstation mit Power Delivery, weil der UNO Q Strom und USB-Geräte
  über denselben Anschluss bekommt

**Wichtig beim Anschließen:** erst die Dockingstation an den Strom, dann die
Webcam an die Dockingstation, zuletzt den Arduino. In anderer Reihenfolge meldet
sich die Dockingstation nicht korrekt als USB-Hub.

**Damit geht:**

- Der Arduino berechnet aus dem Mikrofonsignal ein **Spektrum (FFT)** und schickt
  es per MQTT an den Pi. Dort landet es in der Tabelle `audio_spectrum`.
- Messungen lassen sich als **gut/schlecht** labeln. Das ist die Grundlage für
  Kapitel G: ML-Verfahren vergleichen, einen **Isolation Forest** trainieren,
  den Anomalie-Detektor bewerten.
- Der **Anomalie-Poller** prüft die Akustikdaten laufend und meldet Auffälligkeiten.
  Das ist später der Auslöser für das Agentensystem (Stufe 4).
- Ein **echter CRISP-DM-Durchlauf** von der Frage bis zum Modell mit eigenen Daten.

**Ohne Modellanlage:** Das Mikrofon braucht keine SPS-Anlage. Denkbar ist jede
Geräuschquelle mit „normalem“ und „auffälligem“ Zustand, etwa ein Lüfter, eine
Ständerbohrmaschine oder ein Förderband aus der Werkstatt.

Code und Einrichtung: [`ArduinoUnoQ/`](ArduinoUnoQ).

---

## Stufe 3 · Echte SPS-Anbindung

**Braucht:**

- mindestens eine SPS mit aktiviertem **OPC-UA-Server**, bei uns S7-1500
- Netzwerkverbindung vom Pi zur SPS. Bei uns hängt der Pi per Ethernet im
  Anlagen-Netz und per WLAN im DMZ-Netz der Schule, damit Schülerrechner nicht
  direkt an die Steuerungen kommen.
- **UAExpert** (kostenlos) zum Durchsuchen der OPC-UA-Knoten

**Einrichtung:**

1. Mit UAExpert die Knoten der SPS exportieren
   (Beispiele und Struktur: [`UAExpertExport/`](UAExpertExport)).
2. Die gewünschten Knoten in Node-RED eintragen und den OPC-UA-Endpoint auf die
   eigene SPS umstellen ([`Raspberry/nodered/README.md`](Raspberry/nodered/README.md)).
3. Den Demo-Server dann nicht mehr starten.

**Damit geht:**

- Echte Prozessdaten wie Bandsensoren und Motorlauf in MariaDB, InfluxDB und Grafana
- **Stationsteams:** In Node-RED hat jede Station einen eigenen Tab. Jedes Team
  fragt nur „seine“ SPS ab, die Daten landen getrennt von den Produktionsdaten
  (`team/<station>/<tag>`).
- **Digitaler Zwilling** mit eigenen Daten. Der Zwilling ist auf unsere
  Modellanlage zugeschnitten, für eine andere Anlage muss das Anlagenschema in
  `Raspberry/web/anlage-zwilling.html` angepasst werden.

**Aus unserer Erfahrung:**

- **Kurze Impulse gehen verloren.** Fährt ein Werkstückträger am Sensor vorbei,
  ist das Signal nur Sekundenbruchteile aktiv. Bei einer Abfrage einmal pro
  Sekunde fehlen dann Ereignisse. Robuster ist ein Flankenzähler in der SPS,
  der hochzählt statt nur kurz auf 1 zu gehen. Das ist zugleich ein gutes
  Unterrichtsproblem.
- **SPS-Uhren stimmen oft nicht.** Wir verwenden deshalb den Zeitstempel von
  Node-RED statt dem der SPS.
- **Lieber wenige Variablen.** Mit vielen Knoten pro Sekunde wird die Abfrage
  langsam. Für den Einstieg reichen Ein-/Ausfahrt-Sensoren und Motor-Rechts-/Linkslauf.

---

## Stufe 4 · Agentensystem

**Braucht:**

- einen PC mit Python, der die MariaDB auf dem Pi erreicht
- optional **LM Studio** für ein lokales Sprachmodell. Ohne Sprachmodell laufen
  alle Agenten mit fester, regelbasierter Logik weiter.
- optional **Claude Desktop** für den MCP-Server; dafür braucht man ein Konto bei Anthropic

**Einrichtung:** `.env` aus der Vorlage anlegen, Python-Umgebung einrichten,
Agenten in der vorgegebenen Reihenfolge starten
([`Agentensystem/README.md`](Agentensystem/README.md),
[`MCPLokalClaudeDesktop/README.md`](MCPLokalClaudeDesktop/README.md)).

**Damit geht:**

- **MCP:** Ein Sprachmodell fragt die Datenbank über Werkzeuge ab, nur lesend.
- **A2A:** Der Orchestrator-Agent verteilt Aufgaben an DB- und Report-Agent.
- **LAP:** Der Wartungs-Agent steuert ein Diagnosegerät, aber erst nach
  ausdrücklicher Sicherheitsbestätigung und nie die Produktionssteuerung.
- Die **Agenten-Konsole** im Leitstand spricht die Agenten live an und zeigt ihren
  Ablauf als Graph.

**Sinnvoll erst mit Stufe 2 oder 3**, weil die Agenten auf echte Anomalien
reagieren sollen.

---

## Stufe 5 · Data Lake

**Braucht:** einen zweiten Rechner mit Docker und mehreren GB freiem RAM,
z. B. Lehrer-PC oder Schulserver. Auf dem Pi läuft der Stack bewusst nicht,
Spark allein braucht zu viel Speicher.

**Einrichtung:** `docker compose up -d` in `DataLake/compose`
([`DataLake/README.md`](DataLake/README.md)).

**Damit geht:** Daten aus der MariaDB als Parquet-Dateien in einen Objektspeicher
übernehmen (MinIO), Tabellen versionieren wie mit Git (Nessie) und in
Jupyter-Notebooks mit Spark auswerten.

---

## Vor dem Start in der eigenen Schule klären

- **Datenschutz:** Ein Mikrofon im Raum (Stufe 2) sollte mit der Schulleitung
  bzw. dem Datenschutzbeauftragten abgesprochen werden. In der Datenbank landen
  Spektren und Kennwerte wie Frequenz und Pegel, keine Tonaufnahmen.
- **Cloud-Sprachmodelle:** Wer Claude Desktop nutzt (Stufe 4), schickt Anfragen
  und Datenbankauszüge an einen externen Anbieter. Mit LM Studio bleibt alles
  im Schulnetz.
- **Netzwerk:** Steuerungen gehören nicht ins normale Schulnetz. Die
  IT-Betreuung frühzeitig einbinden, wenn der Pi zwei Netze verbinden soll.
- **Schülergeräte:** Für die LangGraph-Werkstatt und die ML-Skripte muss Python
  installiert oder freigegeben sein. Auf verwalteten Geräten ist das oft der
  größte Zeitfresser.

## Lizenz und Mitmachen

Die Inhalte stehen unter [CC BY 4.0](LICENSE-CC-BY). Ihr dürft sie also
verwenden, anpassen und weitergeben, solange die Quelle genannt wird. Fragen,
Fehler und Erfahrungen aus dem eigenen Unterricht gerne als
[Issue auf GitHub](https://github.com/FlowTheTensor/Datenkrake/issues).
