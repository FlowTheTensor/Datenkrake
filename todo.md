opc-ua overlay überarbeiten
    NodesAuswahl.txt mit einbeziehen und erklären, wozu sie da ist und wie sie aufgebaut ist.
    Anomalien vom arduino q aus per mqtt an Datenbank melden
    Erklären, wie datenauswertung/anomaliedetektion mit den opc-ua-daten funktionert
    agentensysteme genauer erklären
    harness genauer erklären

Datenkrake.local als Webserver für alle:

    Node-RED: eine gemeinsame Instanz und dieselben Flows
    Grafana/InfluxDB: gemeinsame Daten und Dashboards
    MariaDB/PHP-Dashboard: gemeinsame Messdaten
    Jupyter/Data Lake: sofern zentral betrieben, ebenfalls gemeinsame Instanz beziehungsweise Datenablage
    Leitstand: statisch, verursacht kaum Last
    Das ist bei Node-RED besonders kritisch: Änderungen an Flows durch einen Schüler wirken für alle. Bei Jupyter können sich Schüler gegenseitig Dateien, Sessions oder Rechenleistung wegnehmen.

    Für den Unterricht wäre daher sinnvoll:

        Gemeinsame zentrale Ansicht für Leitstand, Grafana und Messdaten.
        Getrennte Schülerinstanzen für Node-RED und Jupyter.
        Entweder je Schüler ein eigener Container/Port oder ein vorgeschalteter Proxy mit getrennten Benutzerpfaden.
        Schreibzugriffe auf zentrale Node-RED-Flows und produktive Datenbanken schützen.
        Jupyter mit Ressourcenlimits versehen.
        Die aktuelle Architektur ist also eher eine gemeinsame Demonstrations- und Analyseumgebung, nicht eine isolierte Mehrbenutzerumgebung.


Human-in-the-loop für die Safety-Fence-Bestätigung im Orchestrator-Graph ergänzen (aktuell automatisch bestätigt, siehe Agentensystem/README.md "Bekannte Vereinfachungen").



Füllstände:
    Palettenlager1: BL1 voll, 12 Stück: 28396, 30485
                              11 Stück: 25930
                              10 Stück: 23773
    Erst Füllstand messen, wenn Auslagerung abgeschlossen, wenn AL-BG2_Bandsensor_Rechts aktiviert

    Rohlager, Dosenoberteile
        Ultraschallsensor hat sehr große Streuung
        Dosenunterteile verkippt im Turm, ggf. per 3D-Druck Seitenteile als Führung


Beobachtungen digitaler Zwilling
    Seriennummer: 14220 (24.08.2026 09:32:48 - 09:34:56)
    Palettenlager1 und Rohlager Bandsensoren nicht aktiv, aber gleichzeitig Rechtslauf aktiv
    Rohlager Bandsensor rechts und Abfüllen Bandsensor links aktiv und bleiben aktiv
    Transfersystem Roboert Bandsensor rechts bleibt aktiv, links wird nie aktiv
    Kamera, Handling, Presse, Palettenlager2 Bandsensoren nie aktiv. Reihenfolge passt aber

    Code-Check (kein Bug gefunden): Stationszuordnung in Raspberry/web/anlage-zwilling.html
    (EMBEDDED_CONFIG, stationByDbKey, RELEVANT_TAG_RE) und Node-Auswahl in
    UAExpertExport/NodesAuswahl.txt sind für alle betroffenen Stationen identisch aufgebaut
    (BG1_Bandsensor_Links/BG2_Bandsensor_Rechts/MA1.Rechtslauf/Linkslauf pro Station vorhanden,
    Events werden korrekt per station+tag zugeordnet). Die Auffälligkeiten stecken also in den
    realen PLC-Rohdaten dieser Produktion, nicht in der Zwilling-Visualisierung.

    Update nach Subscribe-Experiment (September 2026):
    Node-RED testweise von "read" (1s Polling) auf OPC-UA "subscribe" umgestellt
    (Raspberry/nodered/data/flows_nodesauswahl_subscribe.json), dabei diverse echte Bugs
    gefunden und behoben: fehlende Stations-/Tag-Zuordnung bei subscribe-Benachrichtigungen
    (nur payload/topic/statusCode/Timestamps kommen durch, nicht die selbst mitgegebenen
    Felder station/tag/nodeId/endpoint), fehlende Credentials bei neu vergebenen Endpoint-IDs,
    fehlender Unsubscribe-Mechanismus (alte Tags bleiben nach Änderung an NodesAuswahl.txt aktiv
    abonniert). Auch das PLC-eigene Statusbit sBandSensorLinks/sBandSensorRechts (Outputs) statt
    des rohen Hardware-Eingangs +AL-BG1_Bandsensor_Links/+AL-BG2_Bandsensor_Rechts (Inputs)
    verwendet, in der Annahme, dass dieses von der SPS-Logik abgeleitete Bit stabiler ist.
    Trotzdem blieb die Bandsensor-Unzuverlässigkeit bestehen - verschiedene SamplingIntervals
    (1s, 0.2s, 200ms, 0ms) brachten keine konsistente Verbesserung.
    Entscheidender Test: Derselbe Produktionslauf mit dem alten "read"-Flow (flows.json,
    Polling) lieferte exakt dieselben Daten wie mit "subscribe". Das belegt, dass die Ursache
    nicht im Node-RED-Flow, OPC-UA-Client oder Sampling-Modus liegt, sondern schon so aus der
    SPS kommt (Programmlogik oder Sensorik selbst) - außerhalb dessen, was von hier aus ohne
    Zugriff auf das SPS-Programm behoben werden kann.
    Konsequenz: "read"-Flow (flows.json) bleibt produktiv, subscribe-Variante bleibt als
    Testflow liegen, nicht weiterverfolgt.


