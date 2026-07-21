"""
Historian-Bridge: abonniert dasselbe MQTT-Topic wie der bestehende
subscriber (audio/spectrum) und schreibt die skalaren Messwerte
zusätzlich in den Operational Historian (InfluxDB). Rührt subscriber/
und die MariaDB-Pipeline nicht an - reine Ergänzung.

Bewusst nur die skalaren Felder (peak_freq, peak_db, sample_rate) plus
das Label als Tag - das vollständige FFT-Spektrum bleibt Domäne der
MariaDB, siehe Raspberry/historian/README.md.
"""
import os
import time
import json

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

print("Starting historian bridge...")

MQTT_BROKER = os.environ.get("MQTT_BROKER", "mqtt")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = "audio/spectrum"

INFLUX_URL = os.environ.get("INFLUX_URL", "http://historian:8086")
INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN", "changeMeHistorianToken")
INFLUX_ORG = os.environ.get("INFLUX_ORG", "datenkrake")
INFLUX_BUCKET = os.environ.get("INFLUX_BUCKET", "telemetrie")


def wait_for_influx(client: InfluxDBClient) -> None:
    print("Waiting for InfluxDB...")
    while True:
        try:
            if client.ping():
                print("InfluxDB is ready")
                return
        except Exception as e:
            print(f"InfluxDB not ready: {e}, waiting...")
        time.sleep(5)


def main() -> None:
    influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    wait_for_influx(influx)
    write_api = influx.write_api(write_options=SYNCHRONOUS)

    def on_connect(client, userdata, flags, rc):
        print("Connected to MQTT Broker")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to topic: {MQTT_TOPIC}")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            point = (
                Point("audio_spectrum")
                .tag("label", payload.get("label", "gut"))
                .field("peak_freq", float(payload.get("peak_freq", 0)))
                .field("peak_db", float(payload.get("peak_db", 0)))
                .field("sample_rate", int(payload.get("sample_rate", 16000)))
            )
            write_api.write(bucket=INFLUX_BUCKET, record=point)
            print(f"Historian: peak_db={payload.get('peak_db', 0):.1f} geschrieben")
        except Exception as e:
            print(f"Fehler beim Schreiben in den Historian: {e}")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print("Connecting to MQTT...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print("Starting loop...")
    client.loop_forever()


if __name__ == "__main__":
    main()
