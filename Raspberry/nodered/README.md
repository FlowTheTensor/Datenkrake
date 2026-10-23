<img align="right" src="../../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# OPC-UA → Node-RED → MQTT

Liest Tags von einem OPC-UA-Server (z. B. einer S7-1500/ET200SP) und
veröffentlicht sie als JSON auf dem bestehenden Mosquitto-Broker – auf
einem neuen Topic-Namensraum `plc/#`, ohne das bestehende `audio/spectrum`
anzurühren.

```text
S7-1500 / ET200SP --OPC-UA--> Node-RED --MQTT (plc/...)--> Mosquitto (bestehend)
```

## Ohne echte SPS testen

`../opcua_demo_server/` simuliert eine minimale OPC-UA-Gegenstelle für den
Unterricht, falls keine echte S7-1500/ET200SP im Netz erreichbar ist. Der
mitgelieferte Beispiel-Flow zeigt standardmäßig auf diesen Demo-Server.

## Setup

1. Der produktive Flow liegt versioniert unter `data/flows.json` und wird
   per `git pull` aktualisiert. **Wichtig:** Node-RED läuft mit
   `--userDir /data`, das ist ein Bind-Mount vom Host – eine Flow-Datei
   ausschließlich im Docker-Image (per `COPY`) würde beim Start unsichtbar,
   weil der Host-Ordner sie überdeckt. Fehlt `data/flows.json`, holt
   `../setup_iot_stack.sh` den committeten Stand aus Git zurück.
2. Editor öffnen: `http://datenkrake.local:1880`
3. Im Flow den Endpoint-Node **"SPS-Endpoint"** auf die echte OPC-UA-Adresse
   umstellen (`opc.tcp://<plc-ip>:4840/...`) und im Item-Node
   **"Zykluszeit lesen"** die tatsächliche Node-ID eintragen (die
   mitgelieferte `ns=2;s=Station1.Zykluszeit` passt nur zum Demo-Server).
4. Diesen Ast (Item-Node → Client-Node → Function-Node → MQTT-Out) für
   jeden weiteren Tag/jede weitere Station duplizieren.

## Bestehende Installation aktualisieren

Nach einem `git pull` auf dem Raspberry das Update-Skript aus dem
Repository-Root ausführen:

```bash
sudo ./Raspberry/update_iot_stack.sh
```

Das Skript erstellt zuerst ein Backup von MariaDB und dem Node-RED-
Datenverzeichnis, aktualisiert die Container, spielt die MariaDB-Schemata
für Agenten- und PLC-Telemetrie erneut ein und aktualisiert
`NodesAuswahl.txt`. Bestehende Messdaten bleiben erhalten. Der aktive
Node-RED-Flow bleibt standardmäßig ebenfalls erhalten. Sollen Änderungen,
die im Node-RED-Editor auf dem Raspberry gemacht wurden, verworfen und der im
Repository committete Stand von `data/flows.json` wiederhergestellt werden,
ausdrücklich:

```bash
sudo ./Raspberry/update_iot_stack.sh --sync-nodered-flow
```

Die Backups liegen danach unter `Raspberry/backups/<Zeitstempel>/`. Das
Update-Skript führt keinen `git pull` selbst aus.

## Flow-Verlauf (Änderungen der Schüler sichern)

Jeder Deploy im Node-RED-Editor wird automatisch als Commit in einem
eigenen, lokalen Git-Repo auf dem Raspberry gesichert:
`~/nodered-verlauf`. Dieses Repo ist vom Datenkrake-Repo getrennt, es wird
also nie automatisch etwas nach GitHub übertragen. Eingerichtet wird das
von `setup_iot_stack.sh` bzw. `update_iot_stack.sh` (einzeln:
`sudo ./Raspberry/nodered/verlauf/install_flows_verlauf.sh`). Technisch
beobachtet die systemd-Unit `nodered-verlauf.path` die Datei
`data/flows.json` und startet bei jeder Änderung `verlauf/flows_verlauf.sh`.

Jeder Tab liegt im Verlauf als eigene Datei unter `flows/`
(z. B. `flows/station-03-rohlager-dosen.json`), dazu
`flows/_konfiguration.json` mit den Konfigurations-Nodes. Ändert ein Deploy
mehrere Tabs, entsteht **pro Tab ein eigener Commit** mit dem Tab-Namen als
Autor und einer Zusammenfassung wie `+2 / -0 / ~1 Nodes`
(neu / gelöscht / geändert). Jedes Stationsteam hat so seinen eigenen
Verlauf, obwohl alle im selben Node-RED arbeiten.

```bash
V=./Raspberry/nodered/verlauf

$V/flows_wiederherstellen.sh                                   # letzte Deploys
$V/flows_wiederherstellen.sh station-03-rohlager-dosen.json    # Verlauf eines Tabs
git -C ~/nodered-verlauf show <commit>                         # genaue Änderungen

$V/flows_wiederherstellen.sh <commit> station-03-rohlager-dosen.json  # nur diesen Tab zurück
$V/flows_wiederherstellen.sh <commit>                                 # alle Tabs zurück
```

Beim Zurücksetzen eines einzelnen Tabs bleiben alle anderen Tabs, wie sie
sind. Node-RED wird danach neu gestartet. Zurückspielen löscht nichts: Der
wiederhergestellte Stand wird selbst wieder als neuer Commit gesichert.

Externe Sicherung (optional): Im Verlauf-Repo ein Remote `origin`
eintragen, z. B. ein separates **privates** Repo oder ein Ordner auf einem
Netzlaufwerk. Danach pusht jeder Deploy automatisch dorthin:

```bash
git -C ~/nodered-verlauf remote add origin <url>
```

`flows_cred.json` (verschlüsselte Zugangsdaten der Nodes) wird bewusst
nicht gesichert.

## Stations-Tabs für die Stationsteams

Neben dem produktiven Tab „OPC-UA NodesAuswahl -> MQTT“ gibt es in
`data/flows.json` einen Tab pro SPS-Station („Station 01 Leitstand“ bis
„Station 09 Transfersystem Roboter“). Jeder ist der Arbeitsbereich eines
Stationsteams und enthält die vollständige Kette: Node-Auswahl, OPC-UA-Abfrage
im Sekundentakt, Änderungsfilter und MQTT. Die Hochregallager-Station (.10)
hat keinen Tab, dort steckt ein nicht programmierbarer IPC.

| | Produktiver Tab | Stations-Tab |
|---|---|---|
| Node-Auswahl | `/data/NodesAuswahl.txt` | Template-Node **NodesAuswahl** im Tab, wird bei jedem Deploy als `/data/stationen/NodesAuswahl_<nr>_<station>.txt` gespeichert |
| SPS | alle Stationen | nur die eigene (Tab-Umgebungsvariable `STATION_ENDPOINT`), Zeilen anderer Stationen werden ignoriert |
| MQTT | `plc/<station>/<tag>` → MariaDB (`quelle = 'produktion'`), InfluxDB | `team/<station>/<tag>` → MariaDB (`quelle = 'team'`), nicht in InfluxDB |

Startinhalt jeder Station sind Bandsensor links/rechts und Motor
Rechts-/Linkslauf, beim Leitstand (ohne eigenes Band) die bisherigen
HMI-/MES-Tags. Die Vorlagen liegen in `UAExpertExport/stationen/`. Die Teams
ergänzen weitere Knoten direkt im Template-Node, Kandidaten stehen in den
UAExpert-Exporten der jeweiligen Station (`UAExpertExport/<Station>.txt`).
Die Liste wird nach dem Deploy sofort und danach jede Minute neu geladen.

Die Teamdaten sind von den Produktionsdaten getrennt (Spalte `quelle` in
`plc_telemetry`). In der PLC-Datenansicht (`plcdaten.php`) und im digitalen
Zwilling lässt sich die Datenquelle wählen: Produktion, alle Stationsteams
oder ein einzelnes Team. Bei einem einzelnen Team zeigt der Zwilling dessen
Station mit den Teamdaten und alle anderen mit den Produktionsdaten, dazu
die Zahl der Signalwechsel beider Quellen zum Vergleich. Die Produktionsläufe
(Seriennummer) kommen immer aus der Produktion.

Last: Jede SPS hat damit zwei OPC-UA-Sitzungen (produktiver Tab und
Stations-Tab) und wird zweimal pro Sekunde gelesen. Das ist unkritisch,
solange die Teams das Abfrage-Intervall nicht ohne Absprache verkürzen und
nicht Hunderte Knoten eintragen.

Um die Stations-Tabs auf einen Raspberry zu bringen, der bereits läuft, das
Update mit `--sync-nodered-flow` ausführen. Der bisherige Editor-Stand wird
dabei vorher gesichert (Backup-Ordner und Flow-Verlauf).

## ⚠️ Sicherheitshinweis

Der Node-RED-Editor unter Port 1880 hat **standardmäßig keine
Anmeldung** – jeder im Netz kann Flows lesen und verändern. Für den
Unterricht im geschützten Schulnetz meist akzeptabel, für den
Dauerbetrieb sollte
[Admin-Authentifizierung](https://nodered.org/docs/user-guide/runtime/securing-node-red)
in `settings.js` (liegt nach dem ersten Start in `nodered/data/`)
eingerichtet werden.

## Nachrichtenformat auf `plc/<station>/<tag>`

```json
{
  "station": "station01",
  "tag": "zykluszeit",
  "wert": 8.4,
  "zeitstempel": "2026-07-21T10:15:00.000Z"
}
```

## Flow aus `NodesAuswahl.txt`

Fuer den Unterricht mit mehreren Stationen gibt es einen vorbereiteten Import-
Flow in `data/flows_nodesauswahl.json` (älterer Stand; produktiv läuft
`data/flows.json`).

Eigenschaften:

- liest `/data/NodesAuswahl.txt` ein,
- fragt alle dort gelisteten Node-IDs zyklisch ab,
- sendet nur Wertaenderungen (`rbe`) per MQTT nach `plc/<station>/<tag>`.
- legt die OPC-UA-Endpoints fuer die in der Datei verwendeten IPs an
   (`192.168.36.1:4840` bis `192.168.36.10:4840`) und nutzt Login mit
   Benutzer `MES` und Passwort `training`.

Import in Node-RED:

1. Editor oeffnen (`http://datenkrake.local:1880`)
2. Menu -> Import -> Datei `data/flows_nodesauswahl.json` waehlen
3. Deploy

Hinweis zur Dateiablage:

- Der Flow liest aus `/data/NodesAuswahl.txt` im Container.
- `setup_iot_stack.sh` kopiert `UAExpertExport/NodesAuswahl.txt` beim Setup
   einmalig nach `Raspberry/nodered/data/NodesAuswahl.txt`.
- Wenn sich die Auswahl aendert, Datei im `nodered/data`-Ordner aktualisieren
   (oder Setup erneut ausfuehren) und dann in Node-RED neu deployen.

## Aufgabenstellung für die Schülerinnen und Schüler

### Ziel

Die Schülerinnen und Schüler sollen selbst die Struktur der OPC-UA-Daten eines echten oder simulierten Sensors/Stations erkunden und daraus einen eigenen Node-RED-Flow aufbauen. Dabei geht es nicht darum, nur einen vorgegebenen Flow zu importieren, sondern die Datenquelle selbst zu verstehen, zu analysieren und in ein sinnvolles MQTT-Format zu transformieren.

### Arbeitsauftrag

1. Startet den OPC-UA-Demo-Server oder verbindet euch mit einem vorhandenen OPC-UA-Server im Schulnetz.
2. Öffnet im Browser den Node-RED-Editor unter `http://datenkrake.local:1880`.
3. Legt in Node-RED einen neuen Flow an und fügt zunächst nur einen OPC-UA-Client-Node ein.
4. Erkennt die Verbindung zum Server über die OPC-UA-Endpunktadresse und testet den Zugriff mit einem ersten `Read`-Befehl.
5. Nutzt den "Browse"-Modus oder die OPC-UA-Explorer-Funktion, um die Struktur der Daten zu untersuchen:
   - Welche Namespaces gibt es?
   - Welche Objekte und Variablen sind sichtbar?
   - Welche Variablen enthalten Messwerte?
   - Welche Daten sind lesbar, welche Typen haben sie?
6. Dokumentiert die gefundenen Daten in einer kurzen Tabelle:
   - Stationsname
   - Tag/Variablenname
   - Node-ID
   - Datentyp
   - Beispielwert
7. Baut danach den Flow schrittweise auf:
   - OPC-UA-Client-Node zur Abfrage der Daten
   - Debug-Node zur Prüfung der Rohdaten
   - Function-Node zur Umstrukturierung des Payloads
   - MQTT-Out-Node zum Veröffentlichen auf `plc/<station>/<tag>`
8. Prüft mit dem Debug-Node, ob die Rohdaten richtig eingelesen werden. Passt danach die Funktion so an, dass die Meldungen im späteren MQTT-Format vorliegen.
9. Testet den Flow mit mindestens zwei unterschiedlichen Tags und prüft die MQTT-Ausgabe mit einem zusätzlichen MQTT-Subscriber oder über den Debug-Output in Node-RED.

### Leitfragen

- Welche Informationen sind für eine Messung relevant?
- Wie lässt sich eine Variable eindeutig einer Station zuordnen?
- Wie sieht ein sinnvoller MQTT-Topic aus?
- Welche Informationen müssen in `msg.payload` enthalten sein, damit die Daten später weiterverarbeitet werden können?
- Welche Werte sind konstant und welche ändern sich zyklisch?

### Erwartetes Ergebnis

Ein eigener Node-RED-Flow, der aus der OPC-UA-Datenstruktur die relevanten Messwerte liest und sie als JSON-Nachrichten auf MQTT veröffentlicht. Die Nachrichten sollten dabei dem Muster folgen:

```json
{
  "station": "station01",
  "tag": "zykluszeit",
  "wert": 8.4,
  "zeitstempel": "2026-07-21T10:15:00.000Z"
}
```

### Hinweise für die Umsetzung

- Die Datenstruktur muss nicht vorgegeben sein – sie ist genau das, was die Schülerinnen und Schüler selbst untersuchen sollen.
- Der erste Schritt ist immer die Analyse der Rohdaten mit einem Debug-Node. Erst danach wird ein Function-Node für die Transformation gebaut.
- Wenn der OPC-UA-Server keine echten SPS-Daten liefert, kann der mitgelieferte Demo-Server verwendet werden.
- Die Node-IDs und Bezeichnungen müssen in der Praxis je nach Server und Anlage unterschiedlich sein. Genau das ist Teil der Aufgabe: Sie selbst zu erkennen und sauber im Flow einzubauen.

## Bekannte Einschränkungen

- Die exakte Form von `msg.payload` nach einem OPC-UA-"read" kann sich je
  nach Version von `node-red-contrib-opcua` leicht unterscheiden. Der
  mitgelieferte Function-Node behandelt das defensiv (Array oder
  Einzelwert), trotzdem beim ersten Test den zusätzlichen Debug-Node im
  Flow ("OPC-UA Rohantwort") beobachten und die Function bei Bedarf
  anpassen.
- Die Node-IDs im Beispiel-Flow (`ns=2;s=Station1.Zykluszeit`) sind
  Platzhalter, passend zum mitgelieferten Demo-Server – reale S7-1500-
  Node-IDs sind anlagenspezifisch und müssen vor Ort ermittelt werden
  (z. B. über den "Browse"-Modus von `node-red-contrib-opcua` oder ein
  Tool wie UAExpert).
