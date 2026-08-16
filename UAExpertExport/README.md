<img align="right" src="../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# OPC-UA-Dokumentation der Modellanlage

Diese README bündelt die Signaldokumentation und die Signal-Legende der mit UAExpert exportierten S7-1500-Stationen. Die Rohdaten liegen als `.txt`-Dateien in diesem Ordner.

## Zweck

- Einheitliche Datengrundlage für Node-RED, MQTT und Datenbankaufzeichnung
- Verständliche Signallandkarte für Unterricht und Inbetriebnahme
- Vorbereitung für KI-Training, Predictive Maintenance und MES-Auswertung

Stand der Exporte: `2026-08-05`

## Exportierte Stationen

| Station | Datei | OPC-UA-Endpoint | Datensätze |
| --- | --- | --- | ---: |
| Leitstand | `Leitstand.txt` | `192.168.36.1:4840` | 1000 |
| Palettenlager 1 | `Palettenlager1.txt` | `192.168.36.2:4840` | 200 |
| Rohlager Dosen | `Rohlager Dosen.txt` | `192.168.36.3:4840` | 198 |
| Abfüllen | `Abfüllen.txt` | `192.168.36.4:4840` | 191 |
| Qualität Kamera | `Qualitaet Kamera.txt` | `192.168.36.5:4840` | 210 |
| Handling Saugarm | `Handling Saugarm.txt` | `192.168.36.6:4840` | 194 |
| Presse | `Presse.txt` | `192.168.36.7:4840` | 186 |
| Palettenlager 2 | `Palettenlager2.txt` | `192.168.36.8:4840` | 200 |
| Transfersystem Roboter | `Transfersystem Roboter.txt` | `192.168.36.9:4840` | 172 |
| Transfersystem Hochregallager | `Transfersystem Hochregallager.txt` | `192.168.36.10:4840` | 172 |

Die meisten Stationen besitzen ein ähnliches Grundmodell. Der Leitstand ist die zentrale Sammel- und Steuerinstanz und enthält zusätzliche stationsübergreifende Handshakes und Strukturtypen.

## Gemeinsame OPC-UA-Struktur

1. **Geräte-Metadaten:** `DeviceManual`, Revisionen, Hersteller, Modell, Seriennummer, Softwarestand und `OperatingMode`.
2. **Inputs:** Sensoren, Bedienbits und eingehende Handshake-Signale.
3. **Outputs:** Aktoren, Stellbits und ausgehende Handshake-Signale.
4. **`DataBlocksGlobal/dbMESStation`:** MES-Kennzahlen, Auftragsnummern, Fehler, Füllstände, Mengen und Zustände.
5. **`DataBlocksGlobal/dbOPCLeitstand`:** Auftrags- und Statusaustausch mit dem Leitstand.

## Signalpräfixe

| Präfix | Bedeutung |
| --- | --- |
| `BG` | Binär-/Grenzsensor, Endlage oder Lichtschranke |
| `BL` | Analogwert, zum Beispiel Füllstand |
| `MA` | Motor oder Antrieb |
| `MB` | Ventil, Zylinder, Stopper oder anderer Aktor |
| `e...` | Eingang, Handshake oder Steuerbit |
| `s...` | Status- oder Meldesignal |
| `+AL`, `+AM`, `+AN`, `+AO` | Funktionsgruppen oder Unterbereiche |

## Empfohlene Signalgruppen

| Gruppe | Zweck | Typische Inhalte |
| --- | --- | --- |
| `heartbeat` | Verfügbarkeit und Zustand | `OperatingMode`, `Status_Online`, `Clock` |
| `process_io` | Prozesszustand und Änderungen | Inputs/Outputs, `BG`, `BL`, `MA`, `MB` |
| `mes` | MES- und KPI-Daten | Aufträge, Fehler, Füllstände, Zylinderstatus |
| `order_link` | Auftrags- und Produktbezug | `uvlaVonLeitstandAuftrag` |
| `status_link` | Rückmeldung an den Leitstand | `uzlsZuLeitstandStatus`, `StationStatus` |

## Stationsschwerpunkte

- **Leitstand:** zentrale Auftragsverfolgung, Stationsstatus und Materialfluss.
- **Palettenlager 1 und 2:** Positionen, Stopper, Vereinzeler, Hub und Lagerfüllstände.
- **Rohlager Dosen:** Zuführung, Trennfunktionen und Materialmangel-Erkennung.
- **Abfüllen:** Magazine, Füllstände, Waagen sowie Zylinder- und Stopperzustände.
- **Handling Saugarm:** Vakuum, Hub, Schwenkarm und Werkstückpräsenz.
- **Presse:** Montage-/Demontagehub und `AnalogInduktiv` als positionsnaher Messwert.
- **Qualität Kamera:** Trigger-/Online-Status, Fehler, erkannte Farbe, Kugelanzahl und Belichtung.
- **Transfersysteme:** Stopper, Automatposition, Materialfluss und Blockadeerkennung.

## MQTT-Modell

Empfohlenes Topic-Schema:

```text
fabrik/linie1/<station>/heartbeat
fabrik/linie1/<station>/process_io
fabrik/linie1/<station>/mes
fabrik/linie1/<station>/order_link
fabrik/linie1/<station>/status_link
```

Beispiel einer Nachricht:

```json
{
  "ts": "2026-08-05T10:00:00.000Z",
  "station": "abfuellen",
  "group": "process_io",
  "quality": "Good",
  "values": {
    "+AM-BG11_FuellstandMag1": true,
    "+AN-BG1_WaageGS": true,
    "sWartet": true
  }
}
```

Zeitstempel werden als UTC im ISO-8601-Format übertragen. Der OPC-UA-`StatusCode` sollte als `quality` erhalten bleiben. Arrays und Strukturen sollten über flache Pfadnamen abgebildet werden.

## Datenbankmodell

Für eine robuste Ablage sind drei Tabellen vorgesehen:

- **`opc_raw`:** vollständige Rohhistorie mit Zeitstempel, Station, Node-Pfad, Wert, Datentyp und Qualität.
- **`opc_mes_snapshot`:** verdichtete MES-Daten für schnelle Dashboard- und Auftragsabfragen.
- **`opc_alarm_events`:** ereignisorientierte Alarme mit Zeitraum, Station, Schweregrad und Kontext.

## Sampling und Datenqualität

- Prozessbits und MES-Werte zyklisch alle `500–1000 ms` erfassen.
- Bei Flankenwechseln wichtiger Signale zusätzliche Events speichern, etwa `Status_Error`, `sStillstand`, `sInReset`, Stopper, Hub und Vakuum.
- Nur Werte mit `quality = Good` für Modelltraining verwenden.
- Fehlende oder ungültige Werte sichtbar als eigene Datenqualitätsklasse markieren.

## KPI- und Analyseideen

- Taktzeit je Station
- Stillstandsquote
- Mikrostau- und Materialmangel-Indikator
- Qualitätsdrift der Kamera
- Hub-/Stopper-Schaltzyklen pro Stunde
- Verweilzeiten in Warte- und Reset-Zuständen

## Umsetzung im Projekt

1. Pro Station einen OPC-UA-Client-Flow in Node-RED anlegen.
2. Signale in die fünf Gruppen einordnen und als MQTT-JSON veröffentlichen.
3. Rohdaten zuerst in `opc_raw` schreiben und anschließend für MES-Abfragen verdichten.
4. Labels aus Fehlern, Ereignissen und Qualitätsbits für KI-Modelle ableiten.
5. Für `heartbeat` MQTT-Retain verwenden; `process_io` nicht retainen.

## Detaildokumente

- [Vollständige OPC-UA-Signaldokumentation](Dokumentation_OPC_UA_Stationen.md)
- [Signal-Legende der Stationen](Signal_Legende_Stationen.md)
