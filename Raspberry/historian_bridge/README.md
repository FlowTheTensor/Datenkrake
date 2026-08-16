<img align="right" src="../../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# Historian Bridge

Die Bridge schreibt MQTT-Messwerte zusaetzlich nach InfluxDB. Sie verarbeitet die Topics `audio/spectrum` und `plc/#`.

Der Dienst wird automatisch ueber Docker Compose gestartet. Vollstaendige FFT-Spektren bleiben in MariaDB.