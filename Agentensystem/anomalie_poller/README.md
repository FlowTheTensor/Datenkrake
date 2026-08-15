# Anomalie Poller

Dieser Dienst liest Telemetriedaten aus InfluxDB oder MariaDB und erkennt daraus akustische Anomalien. Erkannte Ereignisse werden in MariaDB gespeichert.

## Start

```text
python -m anomalie_poller.poller
```

Der Poller arbeitet standardmaessig in einem Intervall von 15 Sekunden. Er ist als Uebergangsloesung gedacht, bis die Erkennung direkt auf dem Arduino per MQTT erfolgt.