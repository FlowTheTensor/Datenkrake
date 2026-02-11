<?php
// API-Endpoint für JSON-Daten
if (isset($_GET['api']) && $_GET['api'] === 'data') {
    header('Content-Type: application/json');
    
    $servername = "db";
    $username = "sensor";
    $password = "changeMeSensor";
    $dbname = "telemetry";
    
    $conn = new mysqli($servername, $username, $password, $dbname);
    if ($conn->connect_error) {
        echo json_encode(['error' => $conn->connect_error]);
        exit;
    }
    
    // Letzte 100 Werte abfragen, dann umkehren für chronologische Reihenfolge
    $sql = "SELECT * FROM measurements ORDER BY ts DESC LIMIT 100";
    $result = $conn->query($sql);
    
    $data = [];
    while($row = $result->fetch_assoc()) {
        $data[] = $row;
    }
    $conn->close();
    
    // Umkehren für chronologische Reihenfolge (älteste zuerst für Charts)
    $data = array_reverse($data);
    
    echo json_encode($data);
    exit;
}
?>
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Datenbank-Inhalt - Live</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; position: sticky; top: 0; }
        .chart-container { width: 100%; height: 300px; margin-bottom: 20px; }
        .charts-section { background: white; padding-bottom: 20px; border-bottom: 1px solid #ddd; }
        .table-section { max-height: 400px; overflow-y: auto; margin-top: 20px; }
        .status { padding: 10px; margin-bottom: 10px; border-radius: 5px; }
        .status.live { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
        h1 { display: flex; align-items: center; gap: 10px; }
        .live-indicator { width: 12px; height: 12px; background: #28a745; border-radius: 50%; animation: pulse 1s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    </style>
</head>
<body>
    <h1>Messdaten aus der Datenbank <span class="live-indicator" title="Live-Aktualisierung aktiv"></span></h1>
    <div class="status live" id="status">Live-Aktualisierung alle 2 Sekunden | Letzte Aktualisierung: <span id="lastUpdate">-</span></div>
    
    <div class="charts-section">
        <h2>Temperatur über Zeit</h2>
        <div class="chart-container"><canvas id="temperatureChart"></canvas></div>
        
        <h2>Beschleunigung über Zeit</h2>
        <div class="chart-container"><canvas id="accelerationChart"></canvas></div>
    </div>
    
    <div class="table-section">
        <table>
            <thead>
                <tr><th>ID</th><th>Zeitstempel</th><th>Sensor</th><th>AX</th><th>AY</th><th>AZ</th><th>GX</th><th>GY</th><th>GZ</th><th>Temperatur</th><th>Anomaly Score</th><th>Anomaly Flag</th></tr>
            </thead>
            <tbody id="dataTable"></tbody>
        </table>
    </div>

    <script>
        let temperatureChart, accelerationChart;

        // Charts initialisieren
        function initCharts() {
            const ctxTemp = document.getElementById('temperatureChart').getContext('2d');
            temperatureChart = new Chart(ctxTemp, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Temperatur (°C)',
                        data: [],
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        fill: true,
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: { duration: 300 },
                    scales: {
                        x: { display: true, title: { display: true, text: 'Zeit' } },
                        y: { display: true, title: { display: true, text: 'Temperatur (°C)' } }
                    }
                }
            });

            const ctxAcc = document.getElementById('accelerationChart').getContext('2d');
            accelerationChart = new Chart(ctxAcc, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        { label: 'AX', data: [], borderColor: 'rgba(54, 162, 235, 1)', fill: false, tension: 0.1 },
                        { label: 'AY', data: [], borderColor: 'rgba(75, 192, 192, 1)', fill: false, tension: 0.1 },
                        { label: 'AZ', data: [], borderColor: 'rgba(153, 102, 255, 1)', fill: false, tension: 0.1 }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: { duration: 300 },
                    scales: {
                        x: { display: true, title: { display: true, text: 'Zeit' } },
                        y: { display: true, title: { display: true, text: 'Beschleunigung' } }
                    }
                }
            });
        }

        // Daten laden und aktualisieren
        async function loadData() {
            try {
                const response = await fetch('?api=data');
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('status').className = 'status error';
                    document.getElementById('status').innerHTML = 'Fehler: ' + data.error;
                    return;
                }

                // Tabelle aktualisieren (neueste oben)
                const tableBody = document.getElementById('dataTable');
                tableBody.innerHTML = data.slice().reverse().map(row => `
                    <tr>
                        <td>${row.id}</td>
                        <td>${row.ts}</td>
                        <td>${row.sensor}</td>
                        <td>${row.ax}</td>
                        <td>${row.ay}</td>
                        <td>${row.az}</td>
                        <td>${row.gx}</td>
                        <td>${row.gy}</td>
                        <td>${row.gz}</td>
                        <td>${row.temperature}</td>
                        <td>${row.anomaly_score ?? '-'}</td>
                        <td>${row.anomaly_flag ?? '-'}</td>
                    </tr>
                `).join('');

                // Charts aktualisieren
                const timestamps = data.map(r => r.ts);
                const temperatures = data.map(r => parseFloat(r.temperature) || 0);
                const axValues = data.map(r => parseFloat(r.ax) || 0);
                const ayValues = data.map(r => parseFloat(r.ay) || 0);
                const azValues = data.map(r => parseFloat(r.az) || 0);

                temperatureChart.data.labels = timestamps;
                temperatureChart.data.datasets[0].data = temperatures;
                temperatureChart.update('none');

                accelerationChart.data.labels = timestamps;
                accelerationChart.data.datasets[0].data = axValues;
                accelerationChart.data.datasets[1].data = ayValues;
                accelerationChart.data.datasets[2].data = azValues;
                accelerationChart.update('none');

                // Status aktualisieren
                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString('de-DE');
                document.getElementById('status').className = 'status live';
                
            } catch (error) {
                document.getElementById('status').className = 'status error';
                document.getElementById('status').innerHTML = 'Verbindungsfehler: ' + error.message;
            }
        }

        // Initialisierung
        initCharts();
        loadData();
        
        // Alle 2 Sekunden aktualisieren
        setInterval(loadData, 2000);
    </script>
</body>
</html>