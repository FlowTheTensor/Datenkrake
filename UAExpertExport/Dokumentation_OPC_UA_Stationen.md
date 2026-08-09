# OPC-UA Signaldokumentation der Modellanlage

## Zweck dieser Dokumentation
Diese Dokumentation beschreibt die mit UAExpert exportierten OPC-UA-Knoten der vorhandenen S7-1500-Stationen.

Ziele:
- Einheitliche Datengrundlage fuer Node-RED, MQTT und Datenbankaufzeichnung
- Verstaendliche Signallandkarte fuer Unterricht und Inbetriebnahme
- Vorbereitung fuer KI-Training, Predictive Maintenance und MES-Auswertung

Quelle der Daten:
- Alle Dateien im Ordner UAExpertExport mit Endung .txt
- Stand: 2026-08-05

## Geltungsbereich (exportierte Stationen)

| Station | Datei | OPC-UA Endpoint (aus Export) | Datensaetze |
|---|---|---|---:|
| Leitstand | Leitstand.txt | 192.168.36.1:4840 | 1000 |
| Palettenlager 1 | Palettenlager1.txt | 192.168.36.2:4840 | 200 |
| Rohlager Dosen | Rohlager Dosen.txt | 192.168.36.3:4840 | 198 |
| Abfuellen | Abfüllen.txt | 192.168.36.4:4840 | 191 |
| Qualitaet Kamera | Qualitaet Kamera.txt | 192.168.36.5:4840 | 210 |
| Handling Saugarm | Handling Saugarm.txt | 192.168.36.6:4840 | 194 |
| Presse (Montage/Demontage) | Presse.txt | 192.168.36.7:4840 | 186 |
| Palettenlager 2 | Palettenlager2.txt | 192.168.36.8:4840 | 200 |
| Transfersystem Roboter | Transfersystem Roboter.txt | 192.168.36.9:4840 | 172 |
| Transfersystem Hochregallager | Transfersystem Hochregallager.txt | 192.168.36.10:4840 | 172 |

Hinweis:
- Die meisten Anlagenstationen haben ein nahezu identisches Kommunikations-Grundmodell.
- Der Leitstand bildet die Zentrale und hat deutlich mehr Signale und eigene Strukturtypen.

## Gemeinsame OPC-UA Grundstruktur je Station

Fast alle Stationsdateien enthalten folgende Ordner/Knotenbereiche:

1. Geraete-Metadaten
- DeviceManual, DeviceRevision, EngineeringRevision
- Manufacturer, Model, SerialNumber, SoftwareRevision
- OperatingMode (typisch: 8 = Run)

2. Inputs
- Sensoren, Bedienbits, Handshake-Eingaenge
- Typisch viele Boolean-Signale, einige UInt16/Int16/UInt32

3. Outputs
- Aktoren, Stellbits, Handshake-Ausgaenge
- Typisch viele Boolean-Signale

4. DataBlocksGlobal/dbMESStation
- MES-relevante Kennzahlen und Strukturfelder
- Beispiel: Arbeitsgang, Auftragsnummern, Fehler, Fuellstaende, Mengen, Zustand

5. DataBlocksGlobal/dbOPCLeitstand
- Auftrags- und Statusaustausch mit Leitstand
- Beispiel: uvlaVonLeitstandAuftrag, uzlsZuLeitstandStatus

## Namenskonventionen (praktische Bedeutung)

Die Bezeichnungen sind nicht offiziell dokumentiert, aber konsistent genug fuer eine belastbare Arbeitsdefinition:

- BG: Grenz-/Binarsensor, Endlage, Lichtschranke
- BL: Analoger Messwert (z. B. Fuellstand)
- MA: Motor/Aktor (haeufig Foerderband)
- MB: Ventil/Zylinder/Ausgangsaktor
- e...: eingehendes Handshake-/Steuersignal
- s...: ausgehendes Status-/Meldesignal

Praefixmuster wie +AL, +AM, +AN, +AO kennzeichnen Unterbereiche bzw. Funktionsgruppen einer Station.

## Einheitliche Signalgruppen fuer Datenbank und MQTT

Empfohlene Gruppierung pro Station:

1. heartbeat
- OperatingMode
- ggf. Clock-Signale (am Leitstand)
- Zweck: Verfuegbarkeit, Offline-Erkennung

2. process_io
- Alle Signals aus Inputs und Outputs
- Zweck: Prozessverlauf, Zyklusanalyse, Stoerungsdiagnose

3. mes
- dbMESStation.*
- Zweck: KPI, Auftragsbezug, Qualitaet, OEE-nahe Kennzahlen

4. order_link
- dbOPCLeitstand.uvlaVonLeitstandAuftrag.*
- Zweck: geplanter Auftrag/Produkt/Weg

5. status_link
- dbOPCLeitstand.uzlsZuLeitstandStatus.*
- Zweck: Rueckmeldung an Leitstand

## Stationsspezifische Hinweise

### Leitstand
Charakteristik:
- Zentrale Sammel- und Steuerinstanz mit 1000 Datensaetzen
- Viele Stationsuebergreifende Handshake-Signale
- Eigene Strukturtypen (z. B. AUFTRAG_VERFOLGUNG, KREUZUNG, DP_BELEGUNG)

Auffaellige Signalgruppen:
- Empfang/SendeProfinet pro Teilstation (BF, DU, H, HR, K, MD, MF, PL)
- Umfangreiche e... / s... Signale fuer Status je Teilanlage
- zusaetzliche Ablauf-/Zentralstrukturen in DataBlocks

Nutzen:
- Beste Quelle fuer End-to-End Materialfluss und Auftragsverfolgung

### Palettenlager 1 und 2
Charakteristik:
- Spiegelbildliche Struktur
- Fokusthemen: Position, Stopper, Vereinzeler, Hub, Fuellstand

Auffaellige Signale:
- +AM-BGx / +AN-BGx fuer Positionen und Endlagen
- +AM-BL1_Fuellstand, +AN-BL2_Fuellstand
- dbMESStation.Fuellstand1..3, iAnzahlLager1..3 im Leitstandstatus

Nutzen:
- Lagerbelegung, Materialnachschub, Verklemmung/Blockade-Erkennung

### Rohlager Dosen
Charakteristik:
- Aehnlich zu Palettenlagern, zusaetzliche Untergruppe AO
- Schwerpunkt auf Zufuehrung und Fuellstandsmanagement

Auffaellige Signale:
- +AM-* und +AO-* fuer zwei Seiten/Funktionsbereiche
- Fuellstandssignale als UInt16 vorhanden

Nutzen:
- Frueherkennung von Materialmangel, Taktverlust durch Leerstand

### Abfuellen
Charakteristik:
- Station fuer Fuell- und Vereinzelungsprozess
- Deutliche Signale zu Magazinen und Waage

Auffaellige Signale:
- FuellstandMag1..3
- WaageGS / WaageAS
- Zylinder-/Stoppersignale in MesZylinder

Nutzen:
- Qualitaetsrelevante Prozesslage, Engpassanalyse, Fuellstandsablaeufe

### Handling Saugarm
Charakteristik:
- Pick-and-Place-artige Funktion
- Vakuum-, Hub- und Schwenkarmzustand klar sichtbar

Auffaellige Signale:
- Vakuum, Hub1/Hub2 oben, Schwenkarm Band/Magazin
- Werkstueckpraesenz

Nutzen:
- Zykluszeit, Fehlgriff-/Vakuumprobleme, mechanische Belastungsindikatoren

### Presse (Montage/Demontage)
Charakteristik:
- Hub- und Stopper-Logik fuer Montage und Demontage
- Ein analoger Induktivwert vorhanden

Auffaellige Signale:
- HubMontageOben/Unten
- HubDemontageOben/Unten
- AnalogInduktiv (Int16)

Nutzen:
- Kraft-/Positionsnahe Proxy-Daten, Erkennung von Press-/Hubabweichungen

### Qualitaet Kamera
Charakteristik:
- Einzige Station mit klaren Kamera-/Vision-Schnittstellensignalen
- Mehrere Command/Status-Knoten fuer Trigger/Ack/Online

Auffaellige Signale:
- Status_Trigger_ready, Status_Data_valid, Status_Error, Status_Online
- Command_Code, Command_Argument, Result_Command_Code, Return_Command_Code
- FarbeErkannt, AnzahlKugeln, Belichtung

Nutzen:
- Qualitaetsmetriken, Bildverarbeitungszustand, Traceability auf Produktebene

### Transfersystem Roboter und Hochregallager
Charakteristik:
- Sehr aehnliche Struktur
- Fokus auf Stopperlogik zwischen GS/AS und Automatposition

Auffaellige Signale:
- Stopper links/rechts fuer AS und GS
- PositionAutomat, StopperAutomat

Nutzen:
- Materialfluss-Synchronisation, Stau- und Taktabweichungen

## Datenmodell fuer MQTT

Empfohlenes Topic-Schema:

- fabrik/linie1/<station>/heartbeat
- fabrik/linie1/<station>/process_io
- fabrik/linie1/<station>/mes
- fabrik/linie1/<station>/order_link
- fabrik/linie1/<station>/status_link

Beispielstationen:
- leitstand
- palettenlager1
- rohlager
- abfuellen
- qualitaet
- handling
- presse
- palettenlager2
- transfer_roboter
- transfer_hochregal

Empfohlenes JSON-Schema pro Message:

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

Hinweise:
- ts immer in UTC (ISO-8601)
- quality aus OPC-UA StatusCode mitgeben
- Bei Arrays/Strukturen flache Key-Namen mit Pfad verwenden

## Datenbankmodell (minimal, robust)

### Tabelle 1: opc_raw
- Zweck: Rohhistorie fuer KI-Training und Re-Processing
- Felder:
  - ts_utc (datetime)
  - station (varchar)
  - node_path (varchar)
  - value_num (double, nullable)
  - value_bool (tinyint, nullable)
  - value_text (text, nullable)
  - datatype (varchar)
  - quality (varchar)

### Tabelle 2: opc_mes_snapshot
- Zweck: schnelle MES-/Dashboard-Abfragen
- Felder:
  - ts_utc
  - station
  - arbeitsgang
  - auftragsnummer
  - zustand
  - menge_produziert
  - menge_ausschuss
  - fehler_code
  - fehler_bezeichnung

### Tabelle 3: opc_alarm_events
- Zweck: Ereignisorientierte Analyse
- Felder:
  - ts_start_utc
  - ts_end_utc
  - station
  - event_key
  - severity
  - context_json

## Sampling- und Logging-Strategie

Empfehlung fuer Unterricht + stabile Datenrate:

1. Zyklische Erfassung
- Prozessbits und MES-Werte alle 500 ms bis 1000 ms

2. Event-basierte Ergaenzung
- Zusaetzlich bei Flankenwechsel von:
  - Status_Error
  - sStillstand
  - sInReset
  - Schluesselsensoren (Stopper, Hub, Vakuum)

3. Datenqualitaet
- Nur Werte mit quality = Good fuer Modelltraining verwenden
- Ungueltige/fehlende Werte als eigene Klasse markieren, nicht still loeschen

## KPI-Vorschlaege fuer KI und Instandhaltung

1. Taktzeit je Station
- Zeit zwischen zwei gueltigen Produkt-/Auftrags-Events

2. Stillstandsquote
- Anteil Zeit mit sStillstand = true

3. Mikrostau-Indikator
- Hauefigkeit schneller Stopper-/Bandsensor-Flanken ohne Auftragsfortschritt

4. Materialmangel-Indikator
- Fuellstandstrends aus BL/Fuellstand-Feldern

5. Qualitaetsdrift
- Bei Kamera: Veraenderungen in FarbeErkannt/AnzahlKugeln/Status_Data_valid

6. Wartungsindikatoren
- Anstieg von Hub-/Stopper-Schaltzyklen pro Stunde
- Zunehmende Verweilzeiten in Warte-/Reset-Zustaenden

## Bekannte Besonderheiten aus den Exporten

- Umlaute kommen in Feldnamen vor (z. B. Fuellstand/Fuellstand mit Umlaut im Original).
- Einzelne Felder haben Schreibvarianten, z. B. SchalterPruefungIgnorieren vs. SchalterPruefungIgnoriren.
- Einige Stationsnamen in dbMESStation.Name stehen auf unknown oder 0 und sollten in der SPS/HMI gepflegt werden.
- Leitstand nutzt zusaetzliche benutzerdefinierte Strukturtypen, die getrennt dokumentiert werden sollten.

## Konkrete Umsetzungsschritte in Ihrem Projekt

1. Node-RED
- Pro Station einen OPC-UA-Client-Flow
- Gruppierung nach den 5 Signalgruppen (heartbeat, process_io, mes, order_link, status_link)
- Ausgabe als MQTT JSON nach obigem Topic-Schema

2. MQTT Broker
- Retain nur fuer heartbeat verwenden
- process_io nicht retainen

3. Datenbank
- Erst in opc_raw schreiben
- Danach per View/ETL in opc_mes_snapshot verdichten

4. KI-Training
- Feature-Store aus opc_raw aufbauen
- Labels aus Ereignissen/Fehlern/Qualitaetsbits erzeugen

## Dateireferenzen

- [UAExpertExport/Leitstand.txt](UAExpertExport/Leitstand.txt)
- [UAExpertExport/Palettenlager1.txt](UAExpertExport/Palettenlager1.txt)
- [UAExpertExport/Rohlager Dosen.txt](UAExpertExport/Rohlager%20Dosen.txt)
- [UAExpertExport/Abfüllen.txt](UAExpertExport/Abf%C3%BCllen.txt)
- [UAExpertExport/Qualitaet Kamera.txt](UAExpertExport/Qualitaet%20Kamera.txt)
- [UAExpertExport/Handling Saugarm.txt](UAExpertExport/Handling%20Saugarm.txt)
- [UAExpertExport/Presse.txt](UAExpertExport/Presse.txt)
- [UAExpertExport/Palettenlager2.txt](UAExpertExport/Palettenlager2.txt)
- [UAExpertExport/Transfersystem Roboter.txt](UAExpertExport/Transfersystem%20Roboter.txt)
- [UAExpertExport/Transfersystem Hochregallager.txt](UAExpertExport/Transfersystem%20Hochregallager.txt)
