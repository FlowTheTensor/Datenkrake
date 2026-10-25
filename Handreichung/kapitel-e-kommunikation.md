# Kapitel E · Kommunikation & Industrie 4.0

[← Übersicht](README.md)

## Worum es geht

Zwei Protokolle, zwei Welten: **OPC-UA** ist der Industriestandard, mit dem die
SPS ihre Daten strukturiert als Baum von Knoten anbietet. **MQTT** ist ein
schlankes Publish/Subscribe-Protokoll aus der IoT-Welt. **Node-RED** übersetzt
zwischen beiden. Es fragt die SPS ab, filtert, verpackt die Werte als JSON und
veröffentlicht sie unter `plc/<station>/<tag>` beim MQTT-Broker Mosquitto.

## Lernziele

Die Schülerinnen und Schüler können …

- OPC-UA und MQTT nach Zweck und Arbeitsweise unterscheiden (Client/Server mit Abfrage vs. Publish/Subscribe über einen Broker),
- einen OPC-UA-Knoten über Endpoint und NodeId adressieren,
- den Weg eines Werts durch einen Node-RED-Flow beschreiben (Abfrage, Änderungsfilter, JSON, MQTT),
- den Aufbau eines MQTT-Topics erklären und Wildcards (`#`) verwenden,
- begründen, warum bei zyklischer Abfrage kurze Impulse verloren gehen können.

## Voraussetzungen

Ausbaustufe 1: Node-RED, Mosquitto und der OPC-UA-Demo-Server genügen für die
Mechanik. Für echte Signale Ausbaustufe 3. UAExpert ist hilfreich, aber nicht
zwingend.

## Zeitbedarf und Ablauf

2–3 DS.

| Phase | Dauer | Inhalt |
| --- | --- | --- |
| Einstieg | 15 min | Kapitel E lesen: Warum zwei Protokolle? |
| OPC-UA | 45 min | Signaldokumentation bzw. UAExpert: Endpoint und NodeId der eigenen Station finden |
| Node-RED | 45 min | Produktiven Flow gemeinsam lesen (nur ansehen!), danach im eigenen Stations-Tab arbeiten |
| MQTT | 30 min | Topics und Wildcards, Werte im Debug-Fenster oder mit einem MQTT-Client mitlesen |
| Vertiefung | 30 min | „Reise eines Messwerts“, Halt 3–5: verlorene Impulse |
| Sicherung | 15 min | Quiz Kapitel E |

## Aufgaben und Musterlösungen

### Lernpfad „Automatisierer“, Schritt 3: OPC-UA, die Adresse eines Werts

> Sucht für eure Station den Endpoint und die NodeId eines Bandsensors heraus.

**Musterlösung für Station Abfüllen:**

- Endpoint: `opc.tcp://192.168.36.4:4840`
- NodeId: `ns=3;s="+AL-BG2_Bandsensor_Rechts"`
- Datentyp: `Boolean`

Die Endpoints der Stationen:

| Station | Endpoint |
| --- | --- |
| Leitstand | 192.168.36.1:4840 |
| Palettenlager 1 | 192.168.36.2:4840 |
| Rohlager Dosen | 192.168.36.3:4840 |
| Abfüllen | 192.168.36.4:4840 |
| Qualität Kamera | 192.168.36.5:4840 |
| Handling Saugarm | 192.168.36.6:4840 |
| Presse | 192.168.36.7:4840 |
| Palettenlager 2 | 192.168.36.8:4840 |
| Transfersystem Roboter | 192.168.36.9:4840 |

Die NodeIds der übrigen Stationen stehen in
[`UAExpertExport/stationen/`](../UAExpertExport/stationen). Erklären sollten die
Schüler die Bestandteile: `ns=3` ist der Namensraum, `s=` heißt, dass der Knoten
über einen Text (String) adressiert wird.

### Lernpfad „Automatisierer“, Schritt 4: Wo gehen Impulse verloren?

> Erklärt, warum ein kurzer Sensorimpuls fehlen kann, und was ein Zähler in der SPS daran ändert.

**Musterlösung:**

- Node-RED **fragt** den Wert nur **einmal pro Sekunde** ab (Read). Bei vielen
  Knoten begrenzt eine Drossel auf 20 Anfragen pro Sekunde, dann wird jeder
  Knoten sogar seltener gelesen.
- Ein Bandsensor-Impuls dauert nur so lange, wie der Magnet unter dem Sensor
  ist. Fällt er **zwischen zwei Abfragen**, sieht Node-RED ihn nie.
- Ein **Flankenzähler in der SPS** zählt bei jeder steigenden Flanke hoch. Die SPS
  sieht jeden Impuls, weil sie im Millisekundentakt arbeitet. Node-RED liest dann
  den **Zählerstand**. Auch bei langsamer Abfrage fehlt nichts, man sieht nur
  später, dass der Zähler gestiegen ist.

**Stufe 4:** zusätzlich die Alternative „Subscribe statt Read“ nennen, bei der
der OPC-UA-Server Änderungen selbst meldet, und ihre Grenzen: Auch der Server
tastet nur in einem bestimmten Intervall ab.

### Lernpfad „Automatisierer“, Schritt 5: MQTT, senden ohne den Empfänger zu kennen

> Erklärt Publish/Subscribe mit eigenen Worten. Wie heißt das Topic, unter dem der Bandsensor eurer Station gesendet wird?

**Musterlösung:**

- Bei **Publish/Subscribe** schickt der Sender seine Nachricht unter einem
  Thema (Topic) an einen **Broker**. Wer sich für das Thema interessiert,
  **abonniert** es beim Broker. Sender und Empfänger kennen sich nicht, und es
  kann beliebig viele Empfänger geben. Ein Vergleich: Radiosender und Radiohörer.
- Topic des Bandsensors bei Abfüllen:
  - Produktion: `plc/abf_llen/AL_BG2_Bandsensor_Rechts`
  - Stationsteam: `team/abf_llen/AL_BG2_Bandsensor_Rechts`
- Aufbau: `plc/<Station>/<Tag>`. Der Stationsname wird kleingeschrieben, und
  alles außer a–z und 0–9 wird durch `_` ersetzt. Aus „Abfüllen“ wird so
  `abf_llen`. Der Tag entsteht aus der NodeId.

**Stufe 4:** die Wildcard erklären. Der Subscriber abonniert `plc/#` und
bekommt damit alle Stationen.

## Typische Schwierigkeiten

- **„Es kommt nichts an.“** Der Änderungsfilter lässt nur **Änderungen** durch.
  Steht ein Sensor still, kommt minutenlang keine Nachricht. Das ist kein Fehler.
- **Umlaute im Topic.** `abf_llen` sieht wie ein Tippfehler aus, ist aber das
  Ergebnis der Ersetzungsregel.
- **Im produktiven Tab arbeiten.** Schüler arbeiten nur in ihrem Stations-Tab.
  Der produktive Tab liefert die Daten für Zwilling und Datenbank.
- **Deploy-Konflikte.** Arbeiten mehrere Teams gleichzeitig, meldet Node-RED
  beim Deploy geänderte Flows. Dann zusammenführen, nicht überschreiben.
- **Abfrageintervall verkürzen.** Das klingt nach einer einfachen Lösung für
  verlorene Impulse, erhöht aber die Last auf allen SPS. Nur nach Absprache.
- **OPC-UA und MQTT gleichsetzen.** Beides „überträgt Daten“, aber OPC-UA
  beschreibt auch, *was* ein Wert ist (Datentyp, Struktur). MQTT transportiert
  nur Nachrichten.

## Bewertung

Woran man Verständnis erkennt:

- Stufe 2: Endpoint, NodeId und Topic der eigenen Station werden gefunden.
- Stufe 3: Der Weg durch den Flow wird in der richtigen Reihenfolge erklärt, einschließlich Änderungsfilter.
- Stufe 4: Verlorene Impulse werden auf die Abfragerate zurückgeführt, und es wird eine Lösung mit ihren Grenzen vorgeschlagen.

Gute Anknüpfung für Kapitel A: Die Startbacklog-Issues 1–3 in der
[Forgejo-README](../Raspberry/forgejo/README.md#startbacklog-opc-ua-daten-verlässlich-abfragen)
greifen genau dieses Problem auf.

## Material im Repo

- [`Raspberry/nodered/`](../Raspberry/nodered): Flows, Stations-Tabs, Flow-Verlauf
- [`UAExpertExport/`](../UAExpertExport): OPC-UA-Dokumentation aller Stationen
- [`Raspberry/opcua_demo_server/`](../Raspberry/opcua_demo_server): Testen ohne SPS
- [`Raspberry/mosquitto/`](../Raspberry/mosquitto): Broker-Konfiguration
- „Reise eines Messwerts“, Halte 2–5
- Quiz Kapitel E auf der Hauptseite
