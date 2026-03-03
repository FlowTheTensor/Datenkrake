import paho.mqtt.client as mqtt
import pymysql
import json
import time
from datetime import datetime

print("Starting audio spectrum subscriber...")

# MQTT settings
MQTT_BROKER = "mqtt"
MQTT_PORT = 1883
MQTT_TOPIC = "audio/spectrum"

# DB settings
DB_HOST = "db"
DB_USER = "sensor"
DB_PASSWORD = "changeMeSensor"
DB_NAME = "telemetry"

def wait_for_db():
    print("Waiting for DB...")
    while True:
        try:
            conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            conn.close()
            print("DB is ready")
            break
        except pymysql.Error as e:
            print(f"DB not ready: {e}, waiting...")
            time.sleep(5)

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker")
    client.subscribe(MQTT_TOPIC)
    print(f"Subscribed to topic: {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Received audio spectrum: peak_freq={payload.get('peak_freq', 0):.1f}Hz, label={payload.get('label', 'unknown')}")

        # Extract data
        label = payload.get("label", "gut")
        peak_freq = payload.get("peak_freq", 0)
        peak_db = payload.get("peak_db", 0)
        spectrum = payload.get("spectrum", [])
        sample_rate = payload.get("sample_rate", 16000)

        # Insert into DB
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        sql = """INSERT INTO audio_spectrum (ts, label, peak_freq, peak_db, spectrum, sample_rate)
                 VALUES (NOW(), %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (label, peak_freq, peak_db, json.dumps(spectrum), sample_rate))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Audio spectrum saved: {label}, {peak_freq:.1f}Hz")

    except Exception as e:
        print(f"Error processing message: {e}")

def main():
    wait_for_db()
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print("Connecting to MQTT...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print("Starting loop...")
    client.loop_forever()

if __name__ == "__main__":
    main()