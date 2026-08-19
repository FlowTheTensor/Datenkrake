opc-ua overlay überarbeiten
    NodesAuswahl.txt mit einbeziehen und erklären, wozu sie da ist und wie sie aufgebaut ist.
    Anomaliegn vom arduino q aus per mqtt an Datenbank melden
    Erklären, wie datenauswertung/anomaliedetektion mit den opc-ua-daten funktionert
    agentensysteme genauer erklären
    harness genauer erklären

vorherige Readme angepasst einbauen

Datenkrake.local als Webserver für alle:

    Node-RED: eine gemeinsame Instanz und dieselben Flows
    Grafana/InfluxDB: gemeinsame Daten und Dashboards
    MariaDB/PHP-Dashboard: gemeinsame Messdaten
    Orange3: eine gemeinsame noVNC-Instanz und standardmäßig ein gemeinsamer Arbeitsbereich
    Jupyter/Data Lake: sofern zentral betrieben, ebenfalls gemeinsame Instanz beziehungsweise Datenablage
    Leitstand: statisch, verursacht kaum Last
    Das ist bei Node-RED besonders kritisch: Änderungen an Flows durch einen Schüler wirken für alle. Bei Orange3 und Jupyter können sich Schüler gegenseitig Dateien, Sessions oder Rechenleistung wegnehmen.

    Für den Unterricht wäre daher sinnvoll:

        Gemeinsame zentrale Ansicht für Leitstand, Grafana und Messdaten.
        Getrennte Schülerinstanzen für Node-RED, Orange3 und Jupyter.
        Entweder je Schüler ein eigener Container/Port oder ein vorgeschalteter Proxy mit getrennten Benutzerpfaden.
        Schreibzugriffe auf zentrale Node-RED-Flows und produktive Datenbanken schützen.
        Orange3 und Jupyter mit Ressourcenlimits versehen.
        Die aktuelle Architektur ist also eher eine gemeinsame Demonstrations- und Analyseumgebung, nicht eine isolierte Mehrbenutzerumgebung.



Probleme
    http://datenkrake.local:80 geht immer noch auf die Akustik-Datenbank-Übersicht, soll aber auf leitstand.html gehen
    Akustigübersicht soll aber weiterhin verfügbar sein und per Link auf leitstand.html erreichbar sein
    Trainingsdaten-Link und Mariadb-Link auf leitstatnd.html zeigen auf gleichen Link -> zusammenfassen
    http://datenkrake.local:8888/  ERR_CONNECTION_REFUSED
    http://datenkrake.local:6080/   ERR_CONNECTION_REFUSED
    http://datenkrake.local:3000/d/opcua-stationen-live/opc-ua-stationen-live   ERR_CONNECTION_REFUSED
    http://datenkrake.local/Raspberry/web/index.php URL not found
    In Node-Red ist nur ein alter Flow, den ich selbst mal lange zuvor erstellt habe sichtbar.

docker ps
    CONTAINER ID   IMAGE                       COMMAND                  CREATED          STATUS                            PORTS                                                                                      NAMES
51bdf32aa842   compose-web                 "docker-php-entrypoi…"   10 minutes ago   Up 9 minutes                      0.0.0.0:80->80/tcp, [::]:80->80/tcp                                                        web-server
2b84ef4fd06f   compose-subscriber          "python3 app.py"         10 minutes ago   Up 9 minutes                                                                                                                 mqtt-subscriber
cb831af38a5c   compose-db                  "docker-entrypoint.s…"   10 minutes ago   Up 9 minutes (healthy)            0.0.0.0:3306->3306/tcp, [::]:3306->3306/tcp                                                mqtt-sql
7b9226acb26c   compose-orange3             "/start.sh"              10 minutes ago   Restarting (127) 31 seconds ago                                                                                              orange3
5840b68d2202   compose-historian_bridge    "python3 app.py"         10 minutes ago   Up 9 minutes                                                                                                                 historian-bridge
c33114bec0aa   compose-opcua_demo_server   "python3 server.py"      10 minutes ago   Up 9 minutes                      0.0.0.0:4840->4840/tcp, [::]:4840->4840/tcp                                                opcua-demo-server
a0ea06990449   grafana/grafana:11.1.4      "/run.sh"                10 minutes ago   Restarting (1) 5 seconds ago                                                                                                 grafana
435f06bf6692   influxdb:2.7                "/entrypoint.sh infl…"   8 days ago       Up 8 days                         0.0.0.0:8086->8086/tcp, [::]:8086->8086/tcp                                                historian
cdaa50f65ec9   105dfb7aa56f                "./entrypoint.sh"        8 days ago       Up 8 days (unhealthy)             0.0.0.0:1880->1880/tcp, [::]:1880->1880/tcp                                                nodered
365deb041b8e   ab0e836867c0                "/docker-entrypoint.…"   2 weeks ago      Up 8 days                         0.0.0.0:1883->1883/tcp, [::]:1883->1883/tcp, 0.0.0.0:9001->9001/tcp, [::]:9001->9001/tcp   mqtt-broker
