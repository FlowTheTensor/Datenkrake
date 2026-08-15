# MariaDB

MariaDB speichert die Audio- und PLC-Telemetrie sowie die Daten des Agentensystems. Die SQL-Dateien im Unterordner `init` legen Datenbanken und Tabellen an.

Der Dienst wird ueber Docker Compose gestartet. Die persistenten Daten liegen im Volume `mariadb/data`.