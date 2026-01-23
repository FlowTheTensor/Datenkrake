import paho.mqtt.client as mqtt
import pymysql
import json
import time
from datetime import datetime

print("Starting subscriber...")

# MQTT settings
MQTT_BROKER = "mqtt"
MQTT_PORT = 1883
MQTT_TOPIC = "sensors/data"

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

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Received message: {payload}")

        # Extract data
        sensor = payload.get("sensor", "default_sensor")
        ax = payload["ax"]
        ay = payload["ay"]
        az = payload["az"]
        gx = payload["gx"]
        gy = payload["gy"]
        gz = payload["gz"]
        temperature = payload.get("temperature")
        anomaly_score = payload.get("anomaly_score")
        anomaly_flag = payload.get("anomaly_flag", 0)

        # Insert into DB
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        sql = """INSERT INTO measurements (ts, sensor, ax, ay, az, gx, gy, gz, temperature, anomaly_score, anomaly_flag)
                 VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (sensor, ax, ay, az, gx, gy, gz, temperature, anomaly_score, anomaly_flag))
        conn.commit()
        cursor.close()
        conn.close()
        print("Data inserted into database")

    except Exception as e:
        print(f"Error processing message: {e}")

def main():
    wait_for_db()  # Warte auf DB
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print("Connecting to MQTT...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print("Starting loop...")
    client.loop_forever()

if __name__ == "__main__":
    main()