<img align="right" src="../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# Datenkrake-IoT-Stack fuer Raspberry Pi

Dieser Ordner enthaelt den zentralen IoT-Stack der Datenkrake. Auf dem Raspberry Pi werden MQTT, MariaDB, InfluxDB, Node-RED, Grafana, die Weboberflaeche, der Historian und der OPC-UA-Demoserver als Docker-Container betrieben.

## Voraussetzungen

- Getestet wurde der Stack ausschliesslich auf einem Raspberry Pi 5 mit 4 GB RAM und Raspberry Pi OS Trixie.
- Raspberry Pi mit Linux und Internetzugang
- Bash, `sudo`, `curl` und `apt-get`
- ein vollstaendiger Checkout dieses Repositorys
- Ausfuehrung des Setup-Skripts mit Root-Rechten

Die Docker-Installation und das Docker-Compose-Plugin werden vom Setup-Skript bei Bedarf eingerichtet.

## Installation

Das Kommando wird aus dem Repository-Root ausgefuehrt:

```bash
sudo ./Raspberry/setup_iot_stack.sh
```

Das Skript legt die persistenten Datenverzeichnisse an, erzeugt die initiale Mosquitto- und Node-RED-Konfiguration, baut die Images, startet die Container und richtet den automatischen Start per systemd ein.

Nach erfolgreicher Installation sind die wichtigsten Oberflaechen unter diesen Adressen erreichbar:

```text
Weboberflaeche: http://<raspberry-ip>/
Grafana:        http://<raspberry-ip>:3000/
Node-RED:       http://<raspberry-ip>:1880/
Forgejo:        http://<raspberry-ip>:3001/
```

### Nach der Installation von Hand

1. **Rechnername `datenkrake`** (am einfachsten schon im Raspberry Pi Imager setzen). Hauptseite, Forgejo und Zwilling verlinken auf `datenkrake.local`; das Setup-Skript weist darauf hin, wenn der Name nicht stimmt.
2. **Ab- und wieder anmelden**, damit der Benutzer Docker ohne `sudo` nutzen kann.
3. **Forgejo einrichten**: Lehrkraft-Konto, Projekt-Repo und Schuelerkonten, siehe [forgejo/README.md](forgejo/README.md#einrichtung-lehrkraft-einmalig).
4. **USB-Stick `DATENKRAKE`** fuer die Datensicherung vorbereiten und einstecken, siehe [backup/README.md](backup/README.md).

Voraussetzung ist ein **64-Bit**-Raspberry-Pi-OS: Das InfluxDB-2-Image gibt es nicht fuer 32 Bit. Der erste Start dauert einige Minuten, weil alle Images gebaut werden; Grafana braucht beim allerersten Start zusaetzlich etwa eine Minute fuer seine Datenbank.

## Update

Das Update-Skript fuehrt keinen Git-Pull aus. Repository zuerst aktualisieren und danach das Skript aus dem Repository-Root starten:

```bash
git pull
sudo ./Raspberry/update_iot_stack.sh
```

Dabei werden vor dem Update Backups von MariaDB und Node-RED erstellt, neue Images geladen bzw. gebaut, die Agentensystem- und PLC-Schemata eingespielt und die betroffenen Dienste neu gestartet.

Der aktive Node-RED-Flow bleibt standardmaessig erhalten. Soll stattdessen die Flow-Vorlage aus dem Repository uebernommen werden:

```bash
sudo ./Raspberry/update_iot_stack.sh --sync-nodered-flow
```

Die Backups liegen unter `Raspberry/backups/<Zeitstempel>/`, also auf derselben SD-Karte. Gegen einen Ausfall von SD-Karte oder Pi schützt erst die Datensicherung auf USB-Stick.

## Datensicherung

Nach jeder Unterrichtsstunde von Hand und täglich um 17:00 automatisch auf einen USB-Stick mit der Bezeichnung `DATENKRAKE`:

```bash
sudo ./Raspberry/backup/datensicherung.sh --auswerfen
```

Stick vorbereiten, Inhalt der Sicherung und Wiederherstellung (auch auf einem neuen Pi): [backup/README.md](backup/README.md).

## Container und Ports

Alle Container sind im Docker-Netzwerk `iot-net` verbunden.

| Compose-Dienst | Container | Host-Port | Zweck |
| --- | --- | --- | --- |
| `mqtt` | `mqtt-broker` | `1883`, `9001` | Mosquitto MQTT-Broker und MQTT-WebSockets |
| `db` | `mqtt-sql` | `3306` | MariaDB fuer Audio-, PLC- und Agentensystemdaten |
| `subscriber` | `mqtt-subscriber` | keine | Speichert MQTT-Nachrichten in MariaDB |
| `web` | `web-server` | `80` | Apache/PHP-Weboberflaeche und Leitstand |
| `historian` | `historian` | `8086` | InfluxDB fuer Zeitreihen |
| `historian_bridge` | `historian-bridge` | keine | Schreibt MQTT-Messwerte nach InfluxDB |
| `grafana` | `grafana` | `3000` | Dashboards fuer InfluxDB-Daten |
| `nodered` | `nodered` | `1880` | OPC-UA-Client und PLC-MQTT-Publisher |
| `opcua_demo_server` | `opcua-demo-server` | `4840` | Simulierter OPC-UA-Server fuer Tests |
| `forgejo` | `forgejo` | `3001`, `2222` | Backlog, Kanban-Board und Deploy-Verlauf fuer das agile Arbeiten |

Die Portzuordnung ist in `compose/docker-compose.yml` definiert. Ein Eintrag "keine" bedeutet, dass der Dienst nur intern ueber das Docker-Netzwerk erreichbar ist.

## Betrieb und Kontrolle

```bash
cd Raspberry/compose
docker compose ps
docker compose logs -f <dienst>
docker compose restart <dienst>
```

Den Gesamtstatus des Stacks zeigt:

```bash
docker compose ps
```

Die Zugangsdaten in der Compose-Konfiguration enthalten Demo-Platzhalter wie `changeMeRoot`, `changeMeGrafana` und `changeMeHistorianToken`. Diese Werte muessen vor einem produktiven Einsatz geaendert und nicht in oeffentlich erreichbaren Netzen verwendet werden.

## Wichtiger Hinweis zum systemd-Start

Das Setup-Skript traegt im Dienst `iot-stack.service` als Arbeitsverzeichnis automatisch den Ordner `Raspberry/compose` des Checkouts ein, aus dem es gestartet wurde. Wird das Repository spaeter verschoben, das Setup-Skript erneut ausfuehren.