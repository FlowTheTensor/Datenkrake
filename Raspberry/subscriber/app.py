import paho.mqtt.client as mqtt
import pymysql
import json
import time
from datetime import datetime

print("Starting audio spectrum subscriber...")

# MQTT settings
MQTT_BROKER = "mqtt"
MQTT_PORT = 1883
MQTT_TOPICS = ["audio/spectrum", "plc/#"]

# DB settings
DB_HOST = "db"
DB_USER = "sensor"
DB_PASSWORD = "changeMeSensor"
DB_NAME = "telemetry"


def parse_iso_datetime(value):
    if not value:
        return None

    try:
        # Node-RED liefert ISO-8601, oft mit "Z".
        cleaned = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def insert_audio_spectrum(payload):
    print(f"Received audio spectrum: peak_freq={payload.get('peak_freq', 0):.1f}Hz, label={payload.get('label', 'unknown')}")

    label = payload.get("label", "gut")
    peak_freq = payload.get("peak_freq", 0)
    peak_db = payload.get("peak_db", 0)
    spectrum = payload.get("spectrum", [])
    sample_rate = payload.get("sample_rate", 16000)

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


def insert_plc_telemetry(topic, payload):
    station = payload.get("station", "unbekannt")
    endpoint = payload.get("endpoint", "")
    node_id = payload.get("nodeId", "")
    tag = payload.get("tag", "")
    datatype = payload.get("datatype", "")
    wert = payload.get("wert")
    ts = parse_iso_datetime(payload.get("zeitstempel"))

    wert_num = None
    wert_bool = None
    wert_text = None

    if isinstance(wert, bool):
        wert_bool = 1 if wert else 0
    elif isinstance(wert, (int, float)):
        wert_num = float(wert)
    elif isinstance(wert, str):
        wert_text = wert[:255]
    elif wert is not None:
        wert_text = json.dumps(wert, ensure_ascii=False)[:255]

    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor()

    if ts:
        sql = """INSERT INTO plc_telemetry
                 (ts, station, endpoint, node_id, tag, datatype, wert_num, wert_bool, wert_text, payload_json, mqtt_topic)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        params = (ts, station, endpoint, node_id, tag, datatype, wert_num, wert_bool, wert_text, json.dumps(payload), topic)
    else:
        sql = """INSERT INTO plc_telemetry
                 (ts, station, endpoint, node_id, tag, datatype, wert_num, wert_bool, wert_text, payload_json, mqtt_topic)
                 VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        params = (station, endpoint, node_id, tag, datatype, wert_num, wert_bool, wert_text, json.dumps(payload), topic)

    cursor.execute(sql, params)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"PLC value saved: {station}/{tag} = {wert}")

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
    for topic in MQTT_TOPICS:
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        if msg.topic == "audio/spectrum":
            insert_audio_spectrum(payload)
        elif msg.topic.startswith("plc/"):
            insert_plc_telemetry(msg.topic, payload)
        else:
            print(f"Skipping unsupported topic: {msg.topic}")

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