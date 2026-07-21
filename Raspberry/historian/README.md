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
