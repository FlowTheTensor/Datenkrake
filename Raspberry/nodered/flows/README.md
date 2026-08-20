<img align="right" src="../../../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# Node-RED-Flows

Dieser Ordner enthaelt die exportierten Node-RED-Flows fuer die Auswahl und
Verarbeitung der Anlagenknoten. Die JSON-Dateien werden vom Node-RED-Container
verwendet und koennen ueber die Node-RED-Oberflaeche weiterbearbeitet werden.

## Flow `flows_nodesauswahl.json`

Der Flow verbindet die in `../data/NodesAuswahl.txt` eingetragenen OPC-UA-
Knoten mit dem MQTT-Broker. Er fragt die Werte zyklisch ab, filtert unveraenderte
Werte heraus und veroeffentlicht nur Aenderungen auf MQTT.

Der Ablauf besteht aus diesen Abschnitten:

1. **Konfiguration laden**

	Ein Inject-Knoten liest beim Start und danach alle fuenf Minuten die Datei
	`/data/NodesAuswahl.txt`. Eine Function-Node zerlegt jede Zeile in Endpoint,
	Stationsname, NodeId und Datentyp und speichert die Auswahl im Flow-Kontext.
	Dadurch kann die Node-Liste geaendert werden, ohne den Flow manuell fuer
	jeden einzelnen OPC-UA-Knoten anzupassen.

2. **OPC-UA-Leseanfragen erzeugen**

	Ein Inject-Knoten startet beim Deploy einmalig und wiederholt sich jede
	Sekunde. Die Function-Node erzeugt fuer alle geladenen Eintraege einzelne
	Read-Messages. Jede Nachricht enthaelt die Ziel-NodeId und die Metadaten,
	die spaeter fuer MQTT und MariaDB benoetigt werden.

3. **Anfragen drosseln und verteilen**

	Eine Delay-Node begrenzt die Rate auf 20 Nachrichten pro Sekunde. Danach
	verteilt ein Switch die Nachrichten anhand des OPC-UA-Endpoints auf die
	konfigurierten OPC-UA-Client-Nodes. So werden die Anfragen auf die jeweils
	passende SPS beziehungsweise Station geleitet.

4. **Werte normalisieren**

	Die Antwort jedes OPC-UA-Clients kann je nach Node-RED-Version oder Datentyp
	unterschiedlich strukturiert sein. Die Function-Node `Wert normalisieren +
	MQTT-Topic` nimmt daraus den eigentlichen Wert, ergaenzt fehlende Stations-
	und Tag-Namen und baut das Topic
	`plc/<station>/<tag>`.

5. **Nur Aenderungen weitergeben**

	Die RBE-Node `Nur Aenderungen` vergleicht den normalisierten Payload getrennt
	pro Topic. Der erste Wert eines Topics wird gesendet; solange derselbe Wert
	erneut gelesen wird, wird keine MQTT-Nachricht erzeugt. Erst bei einer
	Aenderung wird die Nachricht weitergegeben.

6. **MQTT-Nachricht bauen und senden**

	Eine weitere Function-Node verpackt den Wert als JSON mit Stationsname,
	Endpoint, NodeId, Tag, Datentyp, Wert und ISO-Zeitstempel. Die MQTT-Out-Node
	sendet diese Nachricht ueber Mosquitto auf das zuvor gebaute Topic. Ein
	paralleler Debug-Ausgang zeigt die gesendeten Aenderungen in Node-RED an.

Beispiel fuer eine Nachricht:

```json
{
	"station": "Palettenlager1",
  "endpoint": "opc.tcp://192.168.36.2:4840",
  "nodeId": "ns=3;s=...",
  "tag": "AM-BL1_Fuellstand",
  "datatype": "UInt16",
  "wert": 19583,
  "zeitstempel": "2026-08-20T12:00:00.000Z"
}
```

## Palettenlager

Die beiden Palettenlager werden im Flow ausgeschrieben benannt:

| Stationsname | OPC-UA-Endpoint |
| --- | --- |
| `Palettenlager1` | `opc.tcp://192.168.36.2:4840` |
| `Palettenlager2` | `opc.tcp://192.168.36.8:4840` |

Die Zuordnung ist in den UAExpert-Exporten dokumentiert: `Palettenlager1.txt`
verwendet `192.168.36.2`, `Palettenlager2.txt` verwendet `192.168.36.8`.
Die Stationsnamen werden aus `NodesAuswahl.txt` uebernommen und erscheinen
anschliessend auch in den MQTT-Nachrichten und in der Tabelle
`plc_telemetry`.

## Betrieb und Datenablage

Die MQTT-Nachrichten werden vom Subscriber auf Topics unter `plc/#` gelesen
und in der Tabelle `plc_telemetry` der MariaDB gespeichert. Die PLC-
Uebersicht unter `Raspberry/web/plcdaten.php` liest diese Tabelle ueber die
separate PLC-API.

Wichtig: Der Flow fragt zwar jede Sekunde alle ausgewaehlten Nodes ab, sendet
aber wegen der RBE-Node nur Aenderungen. Ein Neustart oder Deploy von Node-RED
setzt den RBE-Zwischenspeicher zurueck; danach wird fuer jedes Topic wieder der
erste gelesene Wert gesendet.