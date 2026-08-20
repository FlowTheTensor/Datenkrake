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