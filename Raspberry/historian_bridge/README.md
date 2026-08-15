# Historian Bridge

Die Bridge schreibt MQTT-Messwerte zusaetzlich nach InfluxDB. Sie verarbeitet die Topics `audio/spectrum` und `plc/#`.

Der Dienst wird automatisch ueber Docker Compose gestartet. Vollstaendige FFT-Spektren bleiben in MariaDB.