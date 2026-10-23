<img align="right" src="../../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# Datensicherung auf USB-Stick

Alle Arbeitsstände des Raspberry werden auf einen USB-Stick gesichert, damit
nichts verloren geht, wenn die SD-Karte oder der ganze Pi ausfällt:

- **von Hand** nach jeder Unterrichtsstunde (ein Befehl, etwa eine Minute),
- **automatisch** jeden Tag um 17:00, wenn der Stick steckt.

## Was gesichert wird

| Datei auf dem Stick | Inhalt | Wie gesichert |
|---|---|---|
| `mariadb-telemetry.sql.gz` | Messdaten (Akustik, PLC Produktion und Stationsteams, Agentensystem) | `mariadb-dump` im laufenden Betrieb |
| `influxdb.tar.gz` | Historian-Zeitreihen | `influx backup` im laufenden Betrieb |
| `forgejo-data.tar.gz` | Issues, Kanban-Board, Konten, Deploy-Verlauf | Ordner `forgejo/data`, Forgejo wird dafür einige Sekunden angehalten |
| `grafana-data.tar.gz` | Dashboards und Einstellungen | Ordner `grafana/data`, Grafana wird dafür einige Sekunden angehalten |
| `nodered-data.tar.gz` | aktive Flows inkl. Stations-Tabs, Node-Auswahl | Ordner `nodered/data` |
| `verlauf-und-zugang.tar.gz` | `~/nodered-verlauf` (Flow-Verlauf) und `~/.config/datenkrake` (Forgejo-Token der Skripte) | Ordner im Home-Verzeichnis |
| `info.txt`, `pruefsummen.sha256` | Zeitpunkt, Vollständigkeit, Repo-Stand und -Pfad, Prüfsummen | |

Nicht gesichert wird, was sich ohnehin neu erzeugen lässt: der Programmcode
(liegt auf GitHub), die Docker-Images (baut das Setup-Skript) und
zwischengespeicherte MQTT-Nachrichten.

Jede Sicherung liegt in einem eigenen Ordner, z. B.
`datenkrake-backups/2026-10-24_1700/`. Eine Sicherung, bei der ein Teil
fehlgeschlagen ist, endet auf `_teilweise`. Aufbewahrt werden die neuesten
**20** Sicherungen. Außerdem werden die ältesten gelöscht, sobald weniger als
2 GB frei sind.

## USB-Stick vorbereiten (einmalig)

Ein Stick ab 16 GB reicht. Er muss die **Bezeichnung `DATENKRAKE`** haben, daran
erkennt das Skript ihn. Format **exFAT**: lesbar unter Windows und Linux, ohne
die 4-GB-Grenze von FAT32.

- **Unter Windows:** Rechtsklick auf den Stick → *Formatieren* → Dateisystem
  *exFAT*, Volumebezeichnung `DATENKRAKE` → *Starten*.
- **Am Raspberry:** Gerät mit `lsblk` heraussuchen (z. B. `/dev/sda1`, **nicht**
  die SD-Karte `mmcblk0`), dann `sudo mkfs.exfat -n DATENKRAKE /dev/sda1`
  (falls der Befehl fehlt: `sudo apt install exfatprogs`).

Der Stick enthält Konten (Passwörter nur als Hash) und alle Messdaten, also
verschlossen aufbewahren. Am sichersten sind **zwei Sticks im Wechsel**, von
denen einer nicht am Pi steckt.

## Sichern

### Nach der Unterrichtsstunde (von Hand)

Stick einstecken, dann im Repo-Ordner auf dem Raspberry:

```bash
sudo ./Raspberry/backup/datensicherung.sh --auswerfen
```

Mit `--auswerfen` wird der Stick danach ausgehängt und kann sofort abgezogen
werden. Ohne die Option bleibt er eingehängt, zum Beispiel wenn er für die
17-Uhr-Sicherung stecken bleiben soll.

Am Ende steht `Sicherung vollständig.`. Erscheint `UNVOLLSTÄNDIG`, nennt die
Meldung den fehlgeschlagenen Teil (meist ist der Dienst nicht gestartet, siehe
`docker compose ps`).

### Automatisch um 17:00

Eingerichtet von `setup_iot_stack.sh` bzw. `update_iot_stack.sh`, einzeln mit
`sudo ./Raspberry/backup/install_datensicherung.sh`. Der Stick muss dafür
stecken. War der Pi um 17:00 ausgeschaltet, wird die Sicherung nicht beim
nächsten Start nachgeholt, damit sie nicht mitten in den Unterricht fällt.

```bash
systemctl list-timers datenkrake-backup.timer     # nächster Termin
journalctl -u datenkrake-backup -n 30             # Ergebnis der letzten Läufe
sudo systemctl start datenkrake-backup            # sofort sichern, Ausgabe im Journal
```

## Wiederherstellen

Das Skript prüft zuerst die Prüfsummen und fragt dann nach. Bestehende Ordner
werden **nicht gelöscht**, sondern in `<ordner>.vor-wiederherstellung-<zeit>`
umbenannt. Ein Fehlgriff lässt sich also rückgängig machen.

```bash
sudo ./Raspberry/backup/wiederherstellen.sh                       # Sicherungen auflisten
sudo ./Raspberry/backup/wiederherstellen.sh 2026-10-24_1700       # alles zurückspielen
sudo ./Raspberry/backup/wiederherstellen.sh 2026-10-24_1700 forgejo nodered   # nur einzelne Teile
```

Teile: `mariadb`, `influxdb`, `forgejo`, `grafana`, `nodered`, `verlauf`.

### Fall 1: Der Pi läuft, aber etwas ist kaputt

Beispiel: Ein Team hat die Flows zerstört oder auf dem Kanban-Board wurde
versehentlich viel gelöscht. Nur den betroffenen Teil zurückspielen:

```bash
sudo ./Raspberry/backup/wiederherstellen.sh 2026-10-24_1700 nodered
```

Für einen einzelnen Stations-Tab ist der Flow-Verlauf feiner als die
Datensicherung, siehe
[Raspberry/nodered/README.md](../nodered/README.md#flow-verlauf-änderungen-der-schüler-sichern).

Achtung bei `mariadb`: Das Zurückspielen ersetzt die Tabellen durch den Stand
der Sicherung. Messwerte, die seitdem dazugekommen sind, gehen dabei verloren.

### Fall 2: SD-Karte oder Pi defekt, Neuaufbau

1. **Raspberry Pi OS** auf eine neue SD-Karte schreiben, mit demselben
   Benutzernamen wie vorher (steht in `info.txt` unter „Benutzer“), und den
   Pi wieder `datenkrake` nennen, damit `datenkrake.local` funktioniert.
2. **Repo klonen**, in denselben Ordner wie vorher (`info.txt`, „Repo-Pfad“):

   ```bash
   git clone https://github.com/FlowTheTensor/Datenkrake.git ~/Datenkrake-Container
   cd ~/Datenkrake-Container
   ```

3. **Stack einrichten.** Das legt alle Container mit leeren Daten an:

   ```bash
   sudo ./Raspberry/setup_iot_stack.sh
   ```

   Danach einmal ab- und wieder anmelden (Docker-Gruppe) und abwarten, bis
   `docker compose ps` in `Raspberry/compose` alle Dienste als *running* zeigt.
4. **Stick einstecken und alles zurückspielen:**

   ```bash
   sudo ./Raspberry/backup/wiederherstellen.sh                 # neueste Sicherung heraussuchen
   sudo ./Raspberry/backup/wiederherstellen.sh 2026-10-24_1700
   ```

5. **Kontrollieren** (nächster Abschnitt) und die beiseitegelegten leeren
   Ordner `*.vor-wiederherstellung-*` löschen.

### Kontrolle nach der Wiederherstellung

| Was | Wo | Erwartung |
|---|---|---|
| Forgejo | <http://datenkrake.local:3001> | Anmelden mit dem bisherigen Konto, Issues und Board sind da |
| Node-RED | <http://datenkrake.local:1880> | Produktiver Tab und Stations-Tabs vorhanden |
| Flow-Verlauf | `./Raspberry/nodered/verlauf/flows_wiederherstellen.sh` | Bisherige Deploys werden gelistet |
| Messdaten | <http://datenkrake.local/plcdaten.php> | Bisherige PLC-Daten, Quelle Produktion und Stationsteams |
| Zwilling | <http://datenkrake.local/anlage-zwilling.html> | Produktionen lassen sich abspielen |
| Grafana | <http://datenkrake.local:3000> | Dashboards zeigen Verlaufsdaten |

Wenn alles stimmt, die beiseitegelegten Ordner löschen:

```bash
sudo rm -rf Raspberry/*/data.vor-wiederherstellung-* ~/nodered-verlauf.vor-wiederherstellung-*
```

## Einstellungen

Über Umgebungsvariablen beim Aufruf, z. B.
`sudo DATENKRAKE_BACKUPS_BEHALTEN=40 ./Raspberry/backup/datensicherung.sh`:

| Variable | Standard | Bedeutung |
|---|---|---|
| `DATENKRAKE_STICK_LABEL` | `DATENKRAKE` | Bezeichnung des Sticks |
| `DATENKRAKE_BACKUPS_BEHALTEN` | `20` | Anzahl aufbewahrter Sicherungen |
| `DATENKRAKE_DB_ROOT_PASSWORT` | `changeMeRoot` | MariaDB-Root-Passwort, falls in der Compose-Datei geändert |
| `DATENKRAKE_INFLUX_TOKEN` | `changeMeHistorianToken` | InfluxDB-Token, falls geändert |
