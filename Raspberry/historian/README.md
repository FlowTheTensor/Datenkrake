# Operational Historian

Ein **Operational Historian** ist eine auf Zeitreihen spezialisierte
Datenbank für Prozess- und Sensordaten (industrielle Vorbilder: OSIsoft PI,
AVEVA Historian; hier: [InfluxDB](https://www.influxdata.com/), quelloffen
und für den Raspberry Pi leicht genug).

## Warum zusätzlich zur MariaDB?

Die bestehende `audio_spectrum`-Tabelle in MariaDB ist bereits eine Art
Zeitreihe (jede Zeile hat einen Zeitstempel `ts`). Ein dedizierter
Historian löst aber Probleme, die bei sehr vielen, sehr häufigen
Messwerten entstehen und die eine relationale Datenbank nicht gut oder nur
mit viel Zusatzaufwand löst:

| | MariaDB (hier: `audio_spectrum`) | Operational Historian (InfluxDB) |
|---|---|---|
| Datenmodell | Zeilen mit beliebigen Spalten, Fremdschlüsseln, JSON | Messpunkt = Zeitstempel + Tags (Label) + Felder (Zahlenwerte) |
| Stärke | komplexe Abfragen, Verknüpfungen (z. B. mit `audio_anomalien`) | sehr hoher Schreibdurchsatz, effiziente Zeitraum-Abfragen |
| Aufbewahrung | manuell per DELETE/Archivierung | eingebaute Retention-Policies (z. B. "nach 90 Tagen automatisch löschen/verdichten") |
| Typische Frage | "Zeig mir alle Anomalien der Station X mit ihren Wartungsereignissen" | "Zeig mir den Verlauf von peak_db der letzten 6 Stunden, minütlich gemittelt" |

Faustregel fürs Unterrichtsgespräch: **MariaDB für strukturierte,
verknüpfte Ereignisse. Historian für hochfrequente Messreihen.** In der
Praxis laufen beide nebeneinander – genau das zeigt dieser Ausbau.

## Ist "zwei Datenbanken parallel" in der Praxis wirklich üblich?

Ja – der Fachbegriff dafür ist **Polyglot Persistence**: bewusst
mehrere Datenbanktypen für unterschiedliche Zugriffsmuster, statt eine
Datenbank für alles zu verbiegen. In der Industrie ist "Historian neben
relationaler Datenbank/MES" seit Jahrzehnten die Normalarchitektur, nicht
die Ausnahme (klassische Kombination: OSIsoft PI oder AVEVA Historian
neben SAP). Im Web-/Software-Bereich ist es ebenso üblich: eine
OLTP-Datenbank für Geschäftsdaten, daneben ein Metriken-/Zeitreihenspeicher
(Prometheus, InfluxDB) fürs Monitoring.

**Ehrlich für den aktuellen Ausbaustand dieses Projekts:** Bei einem
Arduino mit einem Mikrofon ist das Datenvolumen noch nicht dort, wo sich
ein zweiter Dienst *operativ* auszahlt – eine einzelne, gut indizierte
MariaDB-Tabelle kommt mit dieser Menge mühelos klar. Der Historian ist
hier in erster Linie ein **Lerninhalt**, keine Notwendigkeit für die
aktuelle Anlagengröße.

Er zahlt sich in der Praxis an dem Punkt aus, an dem eine der folgenden
Bedingungen zutrifft – und genau das ist laut Ausbauplan für dieses
Projekt absehbar, sobald weitere Sensoren dazukommen:

- **mehrere Sensoren/Stationen** schreiben gleichzeitig (z. B. mehrere
  Arduino UNO Q, oder die für später vorgesehene OPC-UA-Anbindung an
  S7-1500/ET200SP über Node-RED, siehe `../nodered/README.md`)
- **sehr hohe Schreibfrequenz** (viele Messwerte pro Sekunde statt alle
  paar Sekunden)
- der Wunsch nach **automatischer Datenalterung** ("nach 90 Tagen auf
  Stundenmittel verdichten", statt das manuell in MariaDB nachzubauen)

Kurz: **noch nicht nötig, aber ein realistisches Bild davon, wann es
nötig wird** – und die Architektur steht bereits, sodass beim Anschluss
weiterer Sensoren nichts umgebaut werden muss.

## Aufbau

`historian_bridge/` abonniert **dasselbe** MQTT-Topic (`audio/spectrum`)
wie der bestehende `subscriber/` und schreibt zusätzlich (nicht statt
dessen!) in InfluxDB. Die bestehende Pipeline zur MariaDB bleibt komplett
unverändert.

```
Arduino UNO Q --MQTT--> Mosquitto ---> subscriber      ---> MariaDB (bestehend)
                                   \--> historian_bridge ---> InfluxDB (neu)
```

## Zugriff

- Web-UI: `http://datenkrake.local:8086` (Login: `admin` / im Compose-File hinterlegtes Passwort, bitte vor Produktivbetrieb ändern)
- Org: `datenkrake`, Bucket: `telemetrie`
- Beispiel-Query (Flux, im UI unter "Data Explorer"):
  ```flux
  from(bucket: "telemetrie")
    |> range(start: -6h)
    |> filter(fn: (r) => r._measurement == "audio_spectrum")
    |> filter(fn: (r) => r._field == "peak_db")
  ```

## Bekannte Einschränkungen

- Alle Zugangsdaten (`changeMeHistorian...`) sind Platzhalter wie bei den
  übrigen Diensten in diesem Repo – vor einem Produktivbetrieb ändern.
- Das rohe FFT-Spektrum (`spectrum`-Array) wird bewusst NICHT in den
  Historian geschrieben – Zeitreihen-Datenbanken sind für skalare
  Messwerte optimiert, nicht für große verschachtelte Strukturen. Das
  vollständige Spektrum bleibt Domäne der MariaDB.
