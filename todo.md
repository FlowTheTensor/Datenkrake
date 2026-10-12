opc-ua overlay überarbeiten
    NodesAuswahl.txt mit einbeziehen und erklären, wozu sie da ist und wie sie aufgebaut ist.
    Anomalien vom arduino q aus per mqtt an Datenbank melden
    Erklären, wie datenauswertung/anomaliedetektion mit den opc-ua-daten funktionert
    agentensysteme genauer erklären
    harness genauer erklären

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


Vorschläge Bandsensoren Ein-/Ausfahrt (Oktober 2026)
    Ausgangslage: Magnetsensor am Band + Magnet am Werkstückträger, beim Vorbeifahren nur sehr
    kurz aktiv. Vermutung: Der OPC-UA-Server der SPS erfasst/verschickt zu selten, kurze
    Impulse fallen zwischen zwei Abtastungen durch.

    Entscheidender Test (SPS oder Abgriffkette?):
        In UAExpert einen einzelnen Bandsensor (z. B. sBandSensorLinks einer Station) allein
        abonnieren, Sampling Interval 100 ms (bzw. kleinster erlaubter Wert), Queue Size > 1,
        im Data Access View bzw. Trend View einen Werkstückträger vorbeifahren lassen.
        - Impuls in UAExpert sichtbar -> Ursache liegt in der Kette dahinter (Node-RED/DB).
        - Impuls auch in UAExpert nicht sichtbar -> OPC-UA-Server der SPS tastet zu langsam ab
          bzw. der Impuls ist kürzer als das Abtastintervall.
        Zusätzlich im TIA-Portal in den OPC-UA-Servereinstellungen der CPU nachsehen:
        minimales Abtastintervall (Sampling) und minimales Publishing-Intervall. Der Server
        rundet kleinere Client-Anfragen auf diese Werte hoch.
        Hinweis: Bei Queue Size 1 überschreibt das "Aus" ein kurzes "Ein" innerhalb desselben
        Publishing-Intervalls - der Impuls kommt dann trotz Subscribe nie beim Client an.

    Robuste Lösung im SPS-Programm (unabhängig von Abtast-/Publishingrate):
        - Flankenzähler: pro Sensor eine UDInt-Variable, die bei jeder steigenden Flanke (R_TRIG)
          im SPS-Zyklus hochzählt. Node-RED liest nur den Zähler; jede Erhöhung = eine
          Durchfahrt, auch wenn mehrere zwischen zwei Abfragen liegen.
        - Alternativ Speicherbit mit Quittung: SPS setzt Bit bei Flanke, bleibt gesetzt, bis
          Node-RED per OPC-UA-Write zurücksetzt (benötigt Schreibzugriff, ggf. kritisch).
        - Optional: Zeitpunkt der letzten Flanke in der SPS mitschreiben (nur sinnvoll, wenn die
          SPS-Uhr gestellt ist - aktuell stimmen die SPS-Zeitstempel nicht, z. T. falsches Jahr).
        - In einem eigenen DB (z. B. "dbDatenkrake") ablegen, damit die Station unverändert
          bleibt und nur ein zusätzlicher Baustein ergänzt wird.
        - Gilt nicht für das Transfersystem Hochregallager (IPC, nicht programmierbar).


