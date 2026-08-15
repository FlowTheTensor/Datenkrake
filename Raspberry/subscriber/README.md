# MQTT Subscriber

Der Subscriber abonniert MQTT-Nachrichten und speichert Audio- sowie PLC-Daten in MariaDB. Verarbeitet werden die Topics `audio/spectrum` und `plc/#`.

Der Dienst wird automatisch ueber Docker Compose gestartet und wartet beim Start auf MariaDB.