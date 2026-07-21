# OPC-UA → Node-RED → MQTT

Liest Tags von einem OPC-UA-Server (z. B. einer S7-1500/ET200SP) und
veröffentlicht sie als JSON auf dem bestehenden Mosquitto-Broker – auf
einem neuen Topic-Namensraum `plc/#`, ohne das bestehende `audio/spectrum`
anzurühren.

```
S7-1500 / ET200SP --OPC-UA--> Node-RED --MQTT (plc/...)--> Mosquitto (bestehend)
```

## Ohne echte SPS testen

`../opcua_demo_server/` simuliert eine minimale OPC-UA-Gegenstelle für den
Unterricht, falls keine echte S7-1500/ET200SP im Netz erreichbar ist. Der
mitgelieferte Beispiel-Flow zeigt standardmäßig auf diesen Demo-Server.

## Setup

1. `../setup_iot_stack.sh` legt `nodered/data/` an und kopiert die
   Flow-Vorlage aus `flows/flows.json` dorthin (analog zu
   `mosquitto.conf.example` → `mosquitto.conf`). **Wichtig:** Node-RED
   läuft mit `--userDir /data`, das ist ein Bind-Mount vom Host – eine
   Flow-Datei ausschließlich im Docker-Image (per `COPY`) würde beim
   Start unsichtbar, weil der leere Host-Ordner sie überdeckt. Deshalb
   liegt die Vorlage im Repo unter `flows/` und wird erst zur Laufzeit an
   den echten Pfad kopiert.
2. Editor öffnen: `http://datenkrake.local:1880`
3. Im Flow den Endpoint-Node **"SPS-Endpoint"** auf die echte OPC-UA-Adresse
   umstellen (`opc.tcp://<plc-ip>:4840/...`) und im Item-Node
   **"Zykluszeit lesen"** die tatsächliche Node-ID eintragen (die
   mitgelieferte `ns=2;s=Station1.Zykluszeit` passt nur zum Demo-Server).
4. Diesen Ast (Item-Node → Client-Node → Function-Node → MQTT-Out) für
   jeden weiteren Tag/jede weitere Station duplizieren.

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
