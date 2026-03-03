# Datenkrake Raspi - IoT Datenlogging mit MQTT und MariaDB

Dieses Projekt setzt einen MQTT-Broker (Eclipse Mosquitto) und eine MariaDB-Datenbank in Docker-Containern auf einem Raspberry Pi auf. Es dient zum Sammeln und Speichern von Sensordaten (z. B. von Arduino-Boards) über MQTT und deren Persistierung in einer SQL-Datenbank.

## Features
- **MQTT-Broker**: Empfängt Sensordaten über MQTT (Ports 1883 TCP, 9001 WebSocket).
- **MariaDB-Datenbank**: Speichert Daten in der Tabelle `measurements` (mit Spalten für Beschleunigung, Gyroskop, Temperatur, Anomalie-Erkennung).
- **Persistente Volumes**: Daten, Logs und Konfigurationen bleiben bei Container-Neustarts erhalten.
- **Automatische Initialisierung**: Datenbank-Tabelle wird beim ersten Start erstellt.
- **Sicherheit**: MQTT erfordert Authentifizierung; Datenbank hat dedizierte User.

## Voraussetzungen
- Raspberry Pi (empfohlen: Modell 4 mit 4 GB RAM oder mehr).
- Raspberry Pi OS (64-Bit, basierend auf Debian).
- Internetverbindung für Docker-Installation.
- SD-Karte mit mindestens 16 GB (mehr für längeres Logging).

## Installation
1. **Repository klonen oder kopieren**: Übertrage die Projekt-Dateien auf deinen Raspberry Pi (z. B. via SCP oder USB).
2. **Script ausführen**: Navigiere zum Projektordner und führe das Setup-Script aus:
   ```bash
   sudo ./setup_iot_stack.sh
   ```
   - Dies installiert Docker und Docker Compose (falls nicht vorhanden).
   - Erstellt notwendige Verzeichnisse und Volumes.
   - Baut die Container-Images und startet die Services.
3. **Passwörter konfigurieren**:
   - **MQTT**: Erstelle eine Passwortdatei:
     ```bash
     docker run --rm -it -v $(pwd)/mosquitto/config:/mosquitto/config eclipse-mosquitto:2.0 mosquitto_passwd -c /mosquitto/config/passwd <username>
     ```
     Ersetze `<username>` mit einem Usernamen (z. B. `sensor`).
   - **MariaDB**: Bearbeite `compose/docker-compose.yml` und ändere die Umgebungsvariablen (`MARIADB_ROOT_PASSWORD`, `MARIADB_PASSWORD`) zu sicheren Werten.
4. **Neustart**: Nach Änderungen:
   ```bash
   cd compose
   docker compose down && docker compose up -d
   ```

## Verwendung
- **Services starten/stoppen**:
  ```bash
  cd compose
  docker compose up -d    # Starten
  docker compose down     # Stoppen
  docker compose ps       # Status prüfen
  ```
- **Logs anzeigen**:
  ```bash
  docker compose logs mqtt    # MQTT-Logs
  docker compose logs db      # DB-Logs
  ```
- **Datenbank verbinden**: Von einem anderen Gerät (z. B. PC im gleichen Netzwerk):
  ```bash
  mysql -h <pi-ip> -P 3306 -u sensor -p telemetry
  ```
- **MQTT testen**: Verwende einen MQTT-Client (z. B. `mosquitto_pub`):
  ```bash
  mosquitto_pub -h <pi-ip> -p 1883 -u <username> -P <password> -t "sensors/data" -m '{"ax":1.0,"ay":2.0,"az":3.0,"gx":0.1,"gy":0.2,"gz":0.3,"temperature":25.5}'
  ```

## Datenbank-Schema
Die Tabelle `measurements` wird automatisch erstellt:
```sql
CREATE TABLE IF NOT EXISTS measurements (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ts DATETIME NOT NULL,
    sensor TEXT NOT NULL,
    ax REAL NOT NULL,
    ay REAL NOT NULL,
    az REAL NOT NULL,
    gx REAL NOT NULL,
    gy REAL NOT NULL,
    gz REAL NOT NULL,
    temperature REAL,
    anomaly_score REAL,
    anomaly_flag INTEGER DEFAULT 0
);
```
- `ts`: Zeitstempel (wird automatisch gesetzt).
- `sensor`: Sensor-ID (z. B. "arduino1").
- `ax/ay/az`: Beschleunigung (m/s²).
- `gx/gy/gz`: Gyroskop (rad/s).
- `temperature`: Temperatur (°C).
- `anomaly_score/flag`: Für Anomalie-Erkennung (optional).

## Kapazität und Performance
- **Speicher**: Bei 20 GB freiem Speicher ~125 Mio. Datensätze (~160 Bytes/Zeile).
- **Rate**: 20 Datensätze/Sekunde von 10 Clients = ~72 Tage Logging (abhängig von Hardware).
- **Optimierungen**: Bei hoher Last Indizes hinzufügen oder partitionieren.

## Troubleshooting
- **Container starten nicht**: Prüfe Logs mit `docker compose logs`. Stelle sicher, dass Ports 1883/3306 frei sind.
- **MQTT-Verbindung fehlschlägt**: Passwortdatei prüfen; User muss in `/mosquitto/config/passwd` stehen.
- **DB-Fehler**: Root-Passwort in Compose-Datei überprüfen.
- **Speicher voll**: `docker exec mqtt-sql du -sh /var/lib/mysql` prüfen; alte Daten löschen.
- **Performance**: Bei langsamen Inserts RAM erhöhen oder Swap aktivieren.

## Sicherheit
- Ändere alle Standardpasswörter!
- Beschränke Netzwerkzugriff (Firewall auf Pi).
- Verwende TLS für MQTT/DB, wenn exposed.

## Lizenz
Dieses Projekt ist Open-Source. Passe es an deine Bedürfnisse an.

## Kontakt
Bei Fragen: [Deine E-Mail/Kontakt] oder Issue im Repo erstellen.</content>
