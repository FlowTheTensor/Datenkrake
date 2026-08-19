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

// Datenbank leeren
if (isset($_GET['api']) && $_GET['api'] === 'clear_database' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    header('Content-Type: application/json');
    $conn = new mysqli("db", "sensor", "changeMeSensor", "telemetry");
    if ($conn->connect_error) {
        echo json_encode(['error' => $conn->connect_error]);
        exit;
    }
    $result = $conn->query("SELECT COUNT(*) as cnt FROM audio_spectrum");
    $count = (int)$result->fetch_assoc()['cnt'];
    $conn->query("TRUNCATE TABLE audio_spectrum");
    $conn->close();
    echo json_encode(['success' => true, 'deleted' => $count]);
    exit;
}

// Daten exportieren als CSV fuer lokale Orange3/Jupyter-Analyse
if (isset($_GET['api']) && $_GET['api'] === 'export_csv') {
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="datenkrake_audio_spectrum.csv"');

    $conn = new mysqli("db", "sensor", "changeMeSensor", "telemetry");
    if ($conn->connect_error) {
        http_response_code(500);
        echo "error;" . $conn->connect_error . PHP_EOL;
        exit;
    }

    $labelFilter = isset($_GET['label']) ? $_GET['label'] : null;
    if ($labelFilter && in_array($labelFilter, ['gut', 'schlecht'])) {
        $stmt = $conn->prepare("SELECT id, ts, label, peak_freq, peak_db, spectrum, sample_rate FROM audio_spectrum WHERE label = ? ORDER BY ts ASC");
        $stmt->bind_param("s", $labelFilter);
        $stmt->execute();
        $result = $stmt->get_result();
    } else {
        $result = $conn->query("SELECT id, ts, label, peak_freq, peak_db, spectrum, sample_rate FROM audio_spectrum ORDER BY ts ASC");
    }

    $out = fopen('php://output', 'w');
    fputcsv($out, ['id', 'ts', 'label', 'peak_freq', 'peak_db', 'spectrum', 'sample_rate'], ';');
    while ($row = $result->fetch_assoc()) {
        fputcsv($out, [$row['id'], $row['ts'], $row['label'], $row['peak_freq'], $row['peak_db'], $row['spectrum'], $row['sample_rate']], ';');
    }
    fclose($out);
    $conn->close();
    exit;
}

// Daten exportieren als SQL-Insert-Skript fuer lokale Weiterverarbeitung
if (isset($_GET['api']) && $_GET['api'] === 'export_sql') {
    header('Content-Type: application/sql; charset=utf-8');
    header('Content-Disposition: attachment; filename="datenkrake_audio_spectrum.sql"');

    $conn = new mysqli("db", "sensor", "changeMeSensor", "telemetry");
    if ($conn->connect_error) {
        http_response_code(500);
        echo "-- error: " . $conn->connect_error . PHP_EOL;
        exit;
    }

    $labelFilter = isset($_GET['label']) ? $_GET['label'] : null;
    if ($labelFilter && in_array($labelFilter, ['gut', 'schlecht'])) {
        $stmt = $conn->prepare("SELECT id, ts, label, peak_freq, peak_db, spectrum, sample_rate FROM audio_spectrum WHERE label = ? ORDER BY ts ASC");
        $stmt->bind_param("s", $labelFilter);
        $stmt->execute();
        $result = $stmt->get_result();
    } else {
        $result = $conn->query("SELECT id, ts, label, peak_freq, peak_db, spectrum, sample_rate FROM audio_spectrum ORDER BY ts ASC");
    }

    echo "-- Datenkrake audio_spectrum export\n";
    while ($row = $result->fetch_assoc()) {
        $ts = $conn->real_escape_string($row['ts']);
        $label = $conn->real_escape_string($row['label']);
        $peakFreq = $row['peak_freq'] === null ? 'NULL' : (float)$row['peak_freq'];
        $peakDb = $row['peak_db'] === null ? 'NULL' : (float)$row['peak_db'];
        $sampleRate = $row['sample_rate'] === null ? 'NULL' : (int)$row['sample_rate'];
        $spectrum = $conn->real_escape_string($row['spectrum']);
        echo "INSERT INTO audio_spectrum (ts, label, peak_freq, peak_db, spectrum, sample_rate) VALUES ('{$ts}', '{$label}', {$peakFreq}, {$peakDb}, '{$spectrum}', {$sampleRate});\n";
    }
    $conn->close();
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
<?php // Prevent duplicate HTML output
if (!isset($GLOBALS['__DASHBOARD_RENDERED__'])) {
    $GLOBALS['__DASHBOARD_RENDERED__'] = true;
?>
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Audio-Spektrum Dashboard - Live</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f8f8f8; }
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
        .influx-section { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 20px; }
        .influx-section h2 { margin-top: 0; color: #8b1a1a; }
        .influx-links { margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 10px; }
        .influx-link { color: #8b1a1a; font-size: 13px; text-decoration: none; }
        .influx-link:hover { text-decoration: underline; }
        .dashboard-switch { margin-bottom: 12px; display: flex; gap: 10px; flex-wrap: wrap; }
        .switch-btn { padding: 7px 12px; border: 1px solid #ccc; border-radius: 5px; background: #f2f2f2; cursor: pointer; font-size: 13px; }
        .switch-btn.active { background: #8b1a1a; color: white; border-color: #8b1a1a; }
        .grafana-embed { width: 100%; height: 560px; border: 1px solid #ddd; border-radius: 6px; background: #fafafa; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 13px; }
        th { background-color: #f8f8f8; position: sticky; top: 0; }
        .table-wrapper { max-height: 300px; overflow-y: auto; }
        .label-gut { background: #d4edda; color: #155724; padding: 2px 8px; border-radius: 3px; }
        .label-schlecht { background: #f8d7da; color: #721c24; padding: 2px 8px; border-radius: 3px; }
        .btn-danger { padding: 8px 20px; background: #dc3545; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; margin-left: 15px; }
        .btn-danger:hover { background: #c82333; }
        @media (max-width: 900px) {
            .charts-container { grid-template-columns: 1fr; }
        }
    </style>
<?php } // End prevent duplicate HTML ?>
</head>
<body>
    <div class="header">
        <h1 style="margin: 0;">Audio-Spektrum Dashboard <span class="live-indicator" title="Live-Aktualisierung aktiv"></span></h1>
        <div class="logo">
            <span class="logo-underline"><span class="red-dot">j</span>akob</span><span class="red-dot">-</span><span class="logo-underline-red">preh</span><span class="red-dot">-</span><span class="logo-underline">schule</span><span class="red-dot">!</span>
        </div>
    </div>
    <div style="margin-bottom: 15px;">
        <a href="leitstand.html" style="color:#8b1a1a; font-size: 13px;">→ Agentensystem-Leitstand (MCP · A2A · LAP)</a>
    </div>
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
        <a class="filter-btn" style="display:inline-block;text-decoration:none;background:#e8f1ff;color:#0b3d91;" href="?api=export_csv" target="_blank" rel="noopener">📥 CSV exportieren</a>
        <a class="filter-btn" style="display:inline-block;text-decoration:none;background:#e8f1ff;color:#0b3d91;" href="?api=export_sql" target="_blank" rel="noopener">📄 SQL exportieren</a>
        <button class="btn-danger" onclick="clearDatabase()">🗑️ Datenbank leeren</button>
    </div>
    
    <div class="main-data-container">
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

        <div class="influx-section">
            <h2>InfluxDB / Grafana (Zeitreihenansicht)</h2>
            <div class="dashboard-switch">
                <button id="btnOpcuaDashboard" class="switch-btn active" type="button">OPC-UA Stationen</button>
                <button id="btnLiveDashboard" class="switch-btn" type="button">Datenkrake Live</button>
            </div>
            <div class="influx-links">
                <a id="grafanaOpcuaDashboardLink" class="influx-link" href="#" target="_blank" rel="noopener">→ Grafana OPC-UA-Dashboard öffnen</a>
                <a id="grafanaLiveDashboardLink" class="influx-link" href="#" target="_blank" rel="noopener">→ Grafana Live-Dashboard öffnen</a>
                <a id="grafanaRootLink" class="influx-link" href="#" target="_blank" rel="noopener">→ Grafana Startseite öffnen</a>
                <a id="influxLink" class="influx-link" href="#" target="_blank" rel="noopener">→ InfluxDB öffnen</a>
            </div>
            <iframe id="grafanaEmbed" class="grafana-embed" title="Grafana Dashboard" src="about:blank"></iframe>
        </div>
    </div>

    <style>
        .header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .logo {
            font-family: 'Times New Roman', serif;
            font-size: 28px;
            font-weight: normal;
            color: #333;
            letter-spacing: 1px;
            margin-left: 20px;
            margin-bottom: 0;
            margin-top: 0;
            text-align: right;
            line-height: 1.1;
        }
        .logo .red-dot {
            color: #c00;
        }
        .logo-underline {
            display: inline-block;
            border-bottom: 2px solid #333;
            padding-bottom: 2px;
        }
        .logo-underline-red {
            display: inline-block;
            border-bottom: 2px solid #c00;
            padding-bottom: 2px;
        }
        @media (max-width: 600px) {
            .header { flex-direction: column; align-items: flex-start; }
            .logo { margin-left: 0; text-align: left; font-size: 22px; }
        }
        .main-data-container {
            max-width: 1100px;
            margin: 0 auto;
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: stretch;
        }
        .charts-container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 20px;
            width: 100%;
            max-width: 100%;
        }
        .chart-box {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            flex: 1 1 0;
            min-width: 250px;
            max-width: 50%;
            box-sizing: border-box;
        }
        .chart-box h2 {
            margin-top: 0;
            color: #8b1a1a;
            font-size: 16px;
        }
        .chart-container {
            height: 250px;
            width: 100%;
            min-width: 0;
        }
        .table-section {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            width: 100%;
            box-sizing: border-box;
        }
        .table-section h2 {
            margin-top: 0;
            color: #8b1a1a;
        }
        @media (max-width: 900px) {
            .charts-container {
                flex-direction: column;
                gap: 10px;
            }
            .chart-box {
                max-width: 100%;
            }
        }
        @media (max-width: 600px) {
            .main-data-container {
                padding: 0 2px;
            }
            .chart-box, .table-section {
                padding: 6px;
            }
            .chart-container {
                height: 160px;
            }
            th, td {
                font-size: 11px;
            }
        }
    </style>
</head>
<body>
    

    <script>
        let freqChart, spectrumChart;
        let currentFilter = null;
        let grafanaOpcuaDashboard = '';
        let grafanaLiveDashboard = '';

        function setDashboardButtonState(activeId) {
            document.getElementById('btnOpcuaDashboard').classList.toggle('active', activeId === 'opcua');
            document.getElementById('btnLiveDashboard').classList.toggle('active', activeId === 'live');
        }

        function loadGrafanaDashboard(kind) {
            const embed = document.getElementById('grafanaEmbed');
            if (kind === 'live') {
                embed.src = grafanaLiveDashboard;
                setDashboardButtonState('live');
            } else {
                embed.src = grafanaOpcuaDashboard;
                setDashboardButtonState('opcua');
            }
        }

        function initInfluxGrafanaLinks() {
            const host = window.location.hostname || 'datenkrake.local';
            const protocol = window.location.protocol || 'http:';
            grafanaOpcuaDashboard = `${protocol}//${host}:3000/d/opcua-stationen-live/opc-ua-stationen-live?orgId=1&from=now-1h&to=now&kiosk`;
            grafanaLiveDashboard = `${protocol}//${host}:3000/d/datenkrake-live/datenkrake-live?orgId=1&from=now-1h&to=now&kiosk`;
            const grafanaRoot = `${protocol}//${host}:3000/`;
            const influxRoot = `${protocol}//${host}:8086/`;

            document.getElementById('grafanaOpcuaDashboardLink').href = grafanaOpcuaDashboard;
            document.getElementById('grafanaLiveDashboardLink').href = grafanaLiveDashboard;
            document.getElementById('grafanaRootLink').href = grafanaRoot;
            document.getElementById('influxLink').href = influxRoot;

            document.getElementById('btnOpcuaDashboard').addEventListener('click', () => loadGrafanaDashboard('opcua'));
            document.getElementById('btnLiveDashboard').addEventListener('click', () => loadGrafanaDashboard('live'));

            // Standardansicht ist das OPC-UA-Stationsdashboard.
            loadGrafanaDashboard('opcua');
        }

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
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Amplitude (dB)',
                        data: [],
                        borderColor: '#c00',
                        backgroundColor: 'rgba(220,0,0,0.08)',
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: false,
                        tension: 0.1
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

        async function clearDatabase() {
            if (!confirm('Wirklich ALLE Daten aus der Datenbank löschen? Dies kann nicht rückgängig gemacht werden!')) return;
            try {
                const response = await fetch('?api=clear_database', { method: 'POST' });
                const data = await response.json();
                if (data.error) {
                    alert('Fehler: ' + data.error);
                } else {
                    alert(data.deleted + ' Einträge gelöscht.');
                    loadStats();
                    loadData();
                }
            } catch (e) {
                alert('Fehler: ' + e.message);
            }
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
        initInfluxGrafanaLinks();
        loadStats();
        loadData();
        
        setInterval(() => {
            loadStats();
            loadData();
        }, 2000);
    </script>
</body>
</html>