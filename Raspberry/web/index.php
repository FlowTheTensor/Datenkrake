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
    
    // Filter nach Label (optional)
    $labelFilter = isset($_GET['label']) ? $_GET['label'] : null;
    
    // Letzte 100 Werte abfragen
    if ($labelFilter && in_array($labelFilter, ['gut', 'schlecht'])) {
        $sql = "SELECT * FROM audio_spectrum WHERE label = ? ORDER BY ts DESC LIMIT 100";
        $stmt = $conn->prepare($sql);
        $stmt->bind_param("s", $labelFilter);
        $stmt->execute();
        $result = $stmt->get_result();
    } else {
        $sql = "SELECT * FROM audio_spectrum ORDER BY ts DESC LIMIT 100";
        $result = $conn->query($sql);
    }
    
    $data = [];
    while($row = $result->fetch_assoc()) {
        // Spectrum JSON dekodieren
        $row['spectrum'] = json_decode($row['spectrum'], true);
        $data[] = $row;
    }
    $conn->close();
    
    // Umkehren für chronologische Reihenfolge
    $data = array_reverse($data);
    
    echo json_encode($data);
    exit;
}

// Statistik-Endpoint
if (isset($_GET['api']) && $_GET['api'] === 'stats') {
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
    
    $stats = [];
    
    // Anzahl pro Label
    $result = $conn->query("SELECT label, COUNT(*) as count FROM audio_spectrum GROUP BY label");
    while($row = $result->fetch_assoc()) {
        $stats[$row['label']] = (int)$row['count'];
    }
    
    // Gesamtanzahl
    $result = $conn->query("SELECT COUNT(*) as total FROM audio_spectrum");
    $stats['total'] = (int)$result->fetch_assoc()['total'];
    
    $conn->close();
    echo json_encode($stats);
    exit;
}
?>
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Audio-Spektrum Dashboard - Live</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        h1 { display: flex; align-items: center; gap: 10px; color: #8b1a1a; }
        .live-indicator { width: 12px; height: 12px; background: #28a745; border-radius: 50%; animation: pulse 1s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        
        .status { padding: 10px; margin-bottom: 15px; border-radius: 5px; background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
        
        .stats-container { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); min-width: 150px; text-align: center; }
        .stat-card.gut { border-left: 4px solid #28a745; }
        .stat-card.schlecht { border-left: 4px solid #dc3545; }
        .stat-card.total { border-left: 4px solid #007bff; }
        .stat-value { font-size: 32px; font-weight: bold; color: #333; }
        .stat-label { color: #666; margin-top: 5px; }
        
        .filter-container { margin-bottom: 15px; }
        .filter-btn { padding: 8px 20px; margin-right: 10px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }
        .filter-btn.active { color: white; }
        .filter-btn.all { background: #e9ecef; }
        .filter-btn.all.active { background: #007bff; }
        .filter-btn.gut { background: #d4edda; color: #155724; }
        .filter-btn.gut.active { background: #28a745; color: white; }
        .filter-btn.schlecht { background: #f8d7da; color: #721c24; }
        .filter-btn.schlecht.active { background: #dc3545; color: white; }
        
        .charts-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .chart-box { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .chart-box h2 { margin-top: 0; color: #8b1a1a; font-size: 16px; }
        .chart-container { height: 250px; }
        
        .table-section { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .table-section h2 { margin-top: 0; color: #8b1a1a; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 13px; }
        th { background-color: #f8f8f8; position: sticky; top: 0; }
        .table-wrapper { max-height: 300px; overflow-y: auto; }
        .label-gut { background: #d4edda; color: #155724; padding: 2px 8px; border-radius: 3px; }
        .label-schlecht { background: #f8d7da; color: #721c24; padding: 2px 8px; border-radius: 3px; }
        
        @media (max-width: 900px) {
            .charts-container { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <h1>Audio-Spektrum Dashboard <span class="live-indicator" title="Live-Aktualisierung aktiv"></span></h1>
    <div class="status" id="status">Live-Aktualisierung alle 2 Sekunden | Letzte Aktualisierung: <span id="lastUpdate">-</span></div>
    
    <div class="stats-container">
        <div class="stat-card total">
            <div class="stat-value" id="statTotal">0</div>
            <div class="stat-label">Gesamt</div>
        </div>
        <div class="stat-card gut">
            <div class="stat-value" id="statGut">0</div>
            <div class="stat-label">Gut</div>
        </div>
        <div class="stat-card schlecht">
            <div class="stat-value" id="statSchlecht">0</div>
            <div class="stat-label">Schlecht</div>
        </div>
    </div>
    
    <div class="filter-container">
        <button class="filter-btn all active" onclick="setFilter(null)">Alle</button>
        <button class="filter-btn gut" onclick="setFilter('gut')">Nur Gut</button>
        <button class="filter-btn schlecht" onclick="setFilter('schlecht')">Nur Schlecht</button>
    </div>
    
    <div class="charts-container">
        <div class="chart-box">
            <h2>Peak-Frequenz über Zeit</h2>
            <div class="chart-container"><canvas id="freqChart"></canvas></div>
        </div>
        <div class="chart-box">
            <h2>Aktuelles Spektrum</h2>
            <div class="chart-container"><canvas id="spectrumChart"></canvas></div>
        </div>
    </div>
    
    <div class="table-section">
        <h2>Letzte Messungen</h2>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr><th>ID</th><th>Zeitstempel</th><th>Label</th><th>Peak Freq (Hz)</th><th>Peak dB</th><th>Sample Rate</th></tr>
                </thead>
                <tbody id="dataTable"></tbody>
            </table>
        </div>
    </div>

    <script>
        let freqChart, spectrumChart;
        let currentFilter = null;

        function initCharts() {
            const ctxFreq = document.getElementById('freqChart').getContext('2d');
            freqChart = new Chart(ctxFreq, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Peak Frequenz (Hz)',
                        data: [],
                        borderColor: 'rgba(139, 26, 26, 1)',
                        backgroundColor: 'rgba(139, 26, 26, 0.2)',
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
                        y: { display: true, title: { display: true, text: 'Frequenz (Hz)' }, beginAtZero: true }
                    }
                }
            });

            const ctxSpectrum = document.getElementById('spectrumChart').getContext('2d');
            spectrumChart = new Chart(ctxSpectrum, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Amplitude (dB)',
                        data: [],
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: { duration: 300 },
                    scales: {
                        x: { display: true, title: { display: true, text: 'Frequenz (Hz)' } },
                        y: { display: true, title: { display: true, text: 'dB' } }
                    }
                }
            });
        }

        function setFilter(label) {
            currentFilter = label;
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            if (label === null) {
                document.querySelector('.filter-btn.all').classList.add('active');
            } else {
                document.querySelector(`.filter-btn.${label}`).classList.add('active');
            }
            loadData();
        }

        async function loadStats() {
            try {
                const response = await fetch('?api=stats');
                const stats = await response.json();
                document.getElementById('statTotal').textContent = stats.total || 0;
                document.getElementById('statGut').textContent = stats.gut || 0;
                document.getElementById('statSchlecht').textContent = stats.schlecht || 0;
            } catch (error) {
                console.error('Stats error:', error);
            }
        }

        async function loadData() {
            try {
                let url = '?api=data';
                if (currentFilter) {
                    url += '&label=' + currentFilter;
                }
                const response = await fetch(url);
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
                        <td><span class="label-${row.label}">${row.label}</span></td>
                        <td>${parseFloat(row.peak_freq).toFixed(1)}</td>
                        <td>${parseFloat(row.peak_db).toFixed(1)}</td>
                        <td>${row.sample_rate}</td>
                    </tr>
                `).join('');

                // Peak-Frequenz Chart aktualisieren
                const timestamps = data.map(r => r.ts.split(' ')[1]);
                const peakFreqs = data.map(r => parseFloat(r.peak_freq) || 0);

                freqChart.data.labels = timestamps;
                freqChart.data.datasets[0].data = peakFreqs;
                freqChart.update('none');

                // Spektrum des neuesten Eintrags anzeigen
                if (data.length > 0) {
                    const latest = data[data.length - 1];
                    const spectrum = latest.spectrum || [];
                    const sampleRate = latest.sample_rate || 16000;
                    const maxFreq = sampleRate / 2;
                    const freqLabels = spectrum.map((_, i) => Math.round(i * maxFreq / spectrum.length));
                    
                    spectrumChart.data.labels = freqLabels;
                    spectrumChart.data.datasets[0].data = spectrum;
                    spectrumChart.update('none');
                }

                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString('de-DE');
                document.getElementById('status').className = 'status';
                
            } catch (error) {
                document.getElementById('status').className = 'status error';
                document.getElementById('status').innerHTML = 'Verbindungsfehler: ' + error.message;
            }
        }

        initCharts();
        loadStats();
        loadData();
        
        setInterval(() => {
            loadStats();
            loadData();
        }, 2000);
    </script>
</body>
</html>