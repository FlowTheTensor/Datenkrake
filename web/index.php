<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Datenbank-Inhalt</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .chart-container { width: 100%; height: 400px; margin-bottom: 20px; }
        .charts-section { position: sticky; top: 0; background: white; z-index: 10; padding-bottom: 20px; border-bottom: 1px solid #ddd; }
        .table-section { max-height: 60vh; overflow-y: auto; margin-top: 20px; }
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

    // Daten abfragen (für Tabelle und Charts)
    $sql = "SELECT * FROM measurements ORDER BY ts ASC LIMIT 100";
    $result = $conn->query($sql);

    $timestamps = [];
    $temperatures = [];
    $ax_values = [];
    $ay_values = [];
    $az_values = [];

    if ($result->num_rows > 0) {
        echo "<div class='charts-section'>";
        echo "<h2>Temperatur über Zeit</h2>";
        echo "<div class='chart-container'><canvas id='temperatureChart'></canvas></div>";
        
        echo "<h2>Beschleunigung über Zeit</h2>";
        echo "<div class='chart-container'><canvas id='accelerationChart'></canvas></div>";
        echo "</div>";
        
        echo "<div class='table-section'>";
        echo "<table><tr><th>ID</th><th>Zeitstempel</th><th>Sensor</th><th>AX</th><th>AY</th><th>AZ</th><th>GX</th><th>GY</th><th>GZ</th><th>Temperatur</th><th>Anomaly Score</th><th>Anomaly Flag</th></tr>";
        while($row = $result->fetch_assoc()) {
            echo "<tr><td>" . $row["id"]. "</td><td>" . $row["ts"]. "</td><td>" . $row["sensor"]. "</td><td>" . $row["ax"]. "</td><td>" . $row["ay"]. "</td><td>" . $row["az"]. "</td><td>" . $row["gx"]. "</td><td>" . $row["gy"]. "</td><td>" . $row["gz"]. "</td><td>" . $row["temperature"]. "</td><td>" . $row["anomaly_score"]. "</td><td>" . $row["anomaly_flag"]. "</td></tr>";
            
            // Daten für Charts sammeln
            $timestamps[] = $row["ts"];
            $temperatures[] = $row["temperature"] ?? 0;
            $ax_values[] = $row["ax"];
            $ay_values[] = $row["ay"];
            $az_values[] = $row["az"];
        }
        echo "</table>";
        echo "</div>";
    } else {
        echo "Keine Daten gefunden.";
    }

    $conn->close();
    ?>

    <script>
        // Daten aus PHP in JS übertragen
        const timestamps = <?php echo json_encode($timestamps); ?>;
        const temperatures = <?php echo json_encode($temperatures); ?>;
        const axValues = <?php echo json_encode($ax_values); ?>;
        const ayValues = <?php echo json_encode($ay_values); ?>;
        const azValues = <?php echo json_encode($az_values); ?>;

        // Temperatur-Chart
        const ctxTemp = document.getElementById('temperatureChart').getContext('2d');
        new Chart(ctxTemp, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [{
                    label: 'Temperatur (°C)',
                    data: temperatures,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    fill: true
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Zeit'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Temperatur (°C)'
                        }
                    }
                }
            }
        });

        // Beschleunigung-Chart
        const ctxAcc = document.getElementById('accelerationChart').getContext('2d');
        new Chart(ctxAcc, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [{
                    label: 'AX',
                    data: axValues,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    fill: false
                }, {
                    label: 'AY',
                    data: ayValues,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    fill: false
                }, {
                    label: 'AZ',
                    data: azValues,
                    borderColor: 'rgba(153, 102, 255, 1)',
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    fill: false
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Zeit'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Beschleunigung (m/s²)'
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>