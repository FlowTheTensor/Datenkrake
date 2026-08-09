# Signal-Legende fuer die OPC-UA-Stationen

Diese Datei stellt eine praxisnahe Legende fuer die wichtigsten Signale der exportierten Stationen bereit. Ziel ist es, die Rohsignale aus den UAExpert-Exportdateien in verständliche, datenbank- und MQTT-taugliche Kategorien zu übersetzen.

## Grundlegende Bedeutung der Signalpräfixe

- BG: Binär-/Grenzsensor, Endlage, Lichtschranke
- BL: Analogwert, z. B. Füllstand oder Messwert
- MA: Motor oder Antrieb (oft Förderband, Hub, Rotation)
- MB: Ventil, Zylinder, Stoppereinheit oder Aktor
- e...: Eingangssignal, Handshake oder Steuerbit
- s...: Status-/Meldesignal
- +AL, +AM, +AN, +AO: Funktionsgruppen bzw. Unterbereiche einer Station

## Empfohlene Signalgruppen

| Gruppe | Zweck | Typische Felder |
|---|---|---|
| heartbeat | Verfügbarkeit und Zustand | OperatingMode, Status_Online |
| process_io | Prozesszustand und Zustandsänderungen | Inputs/Outputs, BG, BL, MA, MB |
| mes | MES- und KPI-relevante Daten | Auftragsnummer, Fehler, Füllstand, Zylinderstatus |
| order_link | Auftrags- und Produktbezug | uvlaVonLeitstandAuftrag, Auftrag, Produkt |
| status_link | Rückmeldung an den Leitstand | uzlsZuLeitstandStatus, StationStatus |

## Station-by-Station-Legende

### Leitstand

| Signalbereich | Beispielsignale | Bedeutung |
|---|---|---|
| heartbeat | OperatingMode, Clock, Status_Online | Systemverfügbarkeit und zentrale Zustandsüberwachung |
| process_io | BF_*, DU_*, H_*, HR_*, K_*, MD_*, MF_*, PL_* | Teilstationen, Handshakes und Statusbits |
| mes | Auftragsfolge, Fehlerzustände, Belegungsstatus | Materialfluss und Ablaufverfolgung |
| order_link | uvlaVonLeitstandAuftrag | Auftrag und Produktverknüpfung |
| status_link | uzlsZuLeitstandStatus | Statusrückmeldung an die zentrale Steuerung |

### Palettenlager 1 / 2

| Signalbereich | Beispielsignale | Bedeutung |
|---|---|---|
| heartbeat | OperatingMode | Betriebszustand der Anlage |
| process_io | +AM-BGx, +AN-BGx, Stopper, Hub, Vereinzeler | Position, Endlagen, Stoppereinheiten |
| mes | Fuellstand1, Fuellstand2, Fuellstand3, AnzahlLager | Lagerbelegung und Materialnachschub |
| order_link | dbOPCLeitstand.uvlaVonLeitstandAuftrag | Auftrag-/Produktbezug |
| status_link | dbOPCLeitstand.uzlsZuLeitstandStatus | Lagerstatus an den Leitstand |

### Rohlager Dosen

| Signalbereich | Beispielsignale | Bedeutung |
|---|---|---|
| heartbeat | OperatingMode | Anlagenverfügbarkeit |
| process_io | +AM-*, +AO-* | Zuführ- und Trennfunktionen, Zustände |
| mes | Füllstand, Magazinstatus, Zylinderstatus | Materialmangel, Leerstand, Prozessstörungen |
| order_link | dbOPCLeitstand.uvlaVonLeitstandAuftrag | Produkt- und Auftragsbezug |
| status_link | dbOPCLeitstand.uzlsZuLeitstandStatus | Zustandsrückmeldung |

### Abfüllen

| Signalbereich | Beispielsignale | Bedeutung |
|---|---|---|
| heartbeat | OperatingMode | Betriebszustand |
| process_io | FuellstandMag1, FuellstandMag2, FuellstandMag3, WaageGS, WaageAS | Füllstand, Waage, Prozesszustand |
| mes | MesZylinder, Stoppereinheiten, Füllzustand | Qualitäts- und Prozesskontrolle |
| order_link | dbOPCLeitstand.uvlaVonLeitstandAuftrag | Produkt- und Auftragsbezug |
| status_link | dbOPCLeitstand.uzlsZuLeitstandStatus | Rückmeldung an Leitstand |

### Handling Saugarm

| Signalbereich | Beispielsignale | Bedeutung |
|---|---|---|
| heartbeat | OperatingMode | Betriebszustand |
| process_io | Vakuum, Hub1_oben, Hub2_oben, Schwenkarm_Band, Schwenkarm_Magazin | Greifer- und Armzustand |
| mes | Werkstückpräsenz, Zylinderstatus, Fehlerzustand | Zyklus- und Fehleranalyse |
| order_link | dbOPCLeitstand.uvlaVonLeitstandAuftrag | Auftragskontext |
| status_link | dbOPCLeitstand.uzlsZuLeitstandStatus | Anlagestatus |

### Presse

| Signalbereich | Beispielsignale | Bedeutung |
|---|---|---|
| heartbeat | OperatingMode | Betriebszustand |
| process_io | HubMontageOben, HubMontageUnten, HubDemontageOben, HubDemontageUnten, AnalogInduktiv | Positions- und Druck-/Hubzustand |
| mes | Zustandswechsel, Hubabweichung | Prozessabweichung und Wartung |
| order_link | dbOPCLeitstand.uvlaVonLeitstandAuftrag | Produkt-/Auftragsbezug |
| status_link | dbOPCLeitstand.uzlsZuLeitstandStatus | Zustandsrückmeldung |

### Qualität Kamera

| Signalbereich | Beispielsignale | Bedeutung |
|---|---|---|
| heartbeat | OperatingMode, Status_Online | Betriebs- und Vision-System-Verfügbarkeit |
| process_io | Status_Trigger_ready, Status_Data_valid, Status_Error, Command_Code, Result_Command_Code | Bildverarbeitung und Triggerzustand |
| mes | FarbeErkannt, AnzahlKugeln, Belichtung | Qualitäts- und Vision-Metriken |
| order_link | dbOPCLeitstand.uvlaVonLeitstandAuftrag | Produkt-/Auftragskontext |
| status_link | dbOPCLeitstand.uzlsZuLeitstandStatus | Zustandsrückmeldung |

### Transfersystem Roboter / Hochregallager

| Signalbereich | Beispielsignale | Bedeutung |
|---|---|---|
| heartbeat | OperatingMode | Betriebszustand |
| process_io | StopperLinks, StopperRechts, PositionAutomat, StopperAutomat | Materialfluss- und Positionierung |
| mes | Belegung, Position, Blockade | Stau- und Taktabweichung |
| order_link | dbOPCLeitstand.uvlaVonLeitstandAuftrag | Auftragskontext |
| status_link | dbOPCLeitstand.uzlsZuLeitstandStatus | Rückmeldung an den Leitstand |

## Empfehlung fuer die praktische Nutzung

- Alle Signale in die fünf Gruppen heartbeat, process_io, mes, order_link und status_link einordnen.
- Für KI und Predictive Maintenance bevorzugt numerische und Zustandswechsel mit Zeitstempel speichern.
- Für MES und Traceability zusätzlich Auftragsnummer, Produkt, Werkstück-ID und Fehlercodes mitführen.
- Die exakten Namen aus den jeweiligen .txt-Dateien sollten in der finalen Mapping-Tabelle ergänzt werden.
