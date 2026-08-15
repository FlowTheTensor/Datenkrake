# Docker-Compose-Stack

Die Compose-Datei in diesem Ordner startet den zentralen IoT-Stack fuer den Raspberry Pi. Dazu gehoeren MQTT, MariaDB, Weboberflaeche, Historian, Grafana, Node-RED und OPC-UA.

## Start

```text
cd Raspberry/compose
docker compose up -d
```

Die Container verwenden das gemeinsame Docker-Netzwerk `iot-net`.