<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Datenbank-Inhalt</title>
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Messdaten aus der Datenbank</h1>
    <?php
    $servername = "db"; // Container-Name der DB
    $username = "sensor";
    $password = "changeMeSensor";
    $dbname = "telemetry";

    // Verbindung herstellen
    $conn = new mysqli($servername, $username, $password, $dbname);

    // Verbindung prüfen
    if ($conn->connect_error) {
        die("Verbindung fehlgeschlagen: " . $conn->connect_error);
    }

    // Daten abfragen
    $sql = "SELECT * FROM measurements ORDER BY ts DESC LIMIT 100";
    $result = $conn->query($sql);

    if ($result->num_rows > 0) {
        echo "<table><tr><th>ID</th><th>Zeitstempel</th><th>Sensor</th><th>AX</th><th>AY</th><th>AZ</th><th>GX</th><th>GY</th><th>GZ</th><th>Temperatur</th><th>Anomaly Score</th><th>Anomaly Flag</th></tr>";
        while($row = $result->fetch_assoc()) {
            echo "<tr><td>" . $row["id"]. "</td><td>" . $row["ts"]. "</td><td>" . $row["sensor"]. "</td><td>" . $row["ax"]. "</td><td>" . $row["ay"]. "</td><td>" . $row["az"]. "</td><td>" . $row["gx"]. "</td><td>" . $row["gy"]. "</td><td>" . $row["gz"]. "</td><td>" . $row["temperature"]. "</td><td>" . $row["anomaly_score"]. "</td><td>" . $row["anomaly_flag"]. "</td></tr>";
        }
        echo "</table>";
    } else {
        echo "Keine Daten gefunden.";
    }

    $conn->close();
    ?>
</body>
</html>