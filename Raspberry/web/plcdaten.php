<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>PLC-Telemetrie Dashboard - Live</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f8f8f8; }
        .plc-hero-image { display: block; width: 100%; max-width: 1100px; height: 180px; object-fit: contain; object-position: center; margin: 0 auto 14px; }
        h1 { display: flex; align-items: center; gap: 10px; color: #8b1a1a; }
        .live-indicator { width: 12px; height: 12px; background: #28a745; border-radius: 50%; animation: pulse 1s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .status { padding: 10px; margin-bottom: 15px; border-radius: 5px; background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
        .stats-container { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); min-width: 150px; text-align: center; }
        .stat-card.total { border-left: 4px solid #007bff; }
        .stat-card.stations { border-left: 4px solid #28a745; }
        .stat-value { font-size: 32px; font-weight: bold; color: #333; }
        .stat-label { color: #666; margin-top: 5px; }
        .table-section { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .table-section h2 { margin-top: 0; color: #8b1a1a; }
        table { border-collapse: collapse; width: 100%; min-width: 900px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 13px; vertical-align: top; }
        th { background-color: #f8f8f8; position: sticky; top: 0; }
        .table-wrapper { max-height: 560px; overflow: auto; }
        code { white-space: pre-wrap; word-break: break-word; }
        .header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 10px; flex-wrap: wrap; }
        .logo { font-family: 'Times New Roman', serif; font-size: 28px; font-weight: normal; color: #333; letter-spacing: 1px; margin-left: 20px; text-align: right; line-height: 1.1; }
        .logo .red-dot { color: #c00; }
        .logo-underline { display: inline-block; border-bottom: 2px solid #333; padding-bottom: 2px; }
        .logo-underline-red { display: inline-block; border-bottom: 2px solid #c00; padding-bottom: 2px; }
        .page-nav { margin-bottom: 15px; }
        .page-nav a { color: #8b1a1a; font-size: 13px; margin-right: 15px; }
        .main-data-container { max-width: 1100px; margin: 0 auto; width: 100%; }
        @media (max-width: 600px) {
            .header { flex-direction: column; align-items: flex-start; }
            .logo { margin-left: 0; text-align: left; font-size: 22px; }
            .main-data-container { padding: 0 2px; }
            .table-section { padding: 6px; }
            th, td { font-size: 11px; }
        }
    </style>
</head>
<body>
    <img class="plc-hero-image" src="DatenbankPLC.jpg" alt="Datenbank für PLC-Telemetrie">
    <div class="header">
        <h1 style="margin: 0;">PLC-Telemetrie Dashboard <span class="live-indicator" title="Live-Aktualisierung aktiv"></span></h1>
        <div class="logo">
            <span class="logo-underline"><span class="red-dot">j</span>akob</span><span class="red-dot">-</span><span class="logo-underline-red">preh</span><span class="red-dot">-</span><span class="logo-underline">schule</span><span class="red-dot">!</span>
        </div>
    </div>
    <div class="page-nav">
        <a href="index.html">→ Hauptseite</a>
        <a href="audiodaten.php">→ Audio-Daten</a>
    </div>
    <div class="status" id="status">Live-Aktualisierung alle 2 Sekunden | Letzte Aktualisierung: -</div>

    <div class="main-data-container">
        <div class="stats-container">
            <div class="stat-card total">
                <div class="stat-value" id="total">0</div>
                <div class="stat-label">Messwerte</div>
            </div>
            <div class="stat-card stations">
                <div class="stat-value" id="stations">0</div>
                <div class="stat-label">Stationen</div>
            </div>
        </div>
        <div class="table-section">
            <h2>Letzte PLC-Messungen</h2>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr><th>Zeit</th><th>Station</th><th>Endpoint</th><th>Tag</th><th>Datentyp</th><th>Wert</th><th>MQTT-Topic</th></tr>
                    </thead>
                    <tbody id="data"></tbody>
                </table>
            </div>
        </div>
    </div>
<script>
    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
        }[character]));
    }

    function valueOf(row) {
        if (row.wert_num !== null) return row.wert_num;
        if (row.wert_bool !== null) return row.wert_bool ? 'true' : 'false';
        return row.wert_text ?? '';
    }

    async function loadPlcData() {
        try {
            const [dataResponse, statsResponse] = await Promise.all([
                fetch('api/plc.php?action=data'),
                fetch('api/plc.php?action=stats')
            ]);
            const data = await dataResponse.json();
            const stats = await statsResponse.json();
            if (data.error || stats.error) throw new Error(data.error || stats.error);

            document.getElementById('total').textContent = stats.total || 0;
            document.getElementById('stations').textContent = (stats.stations || []).length;
            document.getElementById('data').innerHTML = data.slice().reverse().map(row => `
                <tr>
                    <td>${escapeHtml(row.ts)}</td>
                    <td>${escapeHtml(row.station)}</td>
                    <td>${escapeHtml(row.endpoint)}</td>
                    <td>${escapeHtml(row.tag)}</td>
                    <td>${escapeHtml(row.datatype)}</td>
                    <td>${escapeHtml(valueOf(row))}</td>
                    <td><code>${escapeHtml(row.mqtt_topic)}</code></td>
                </tr>
            `).join('');
            document.getElementById('status').textContent = 'Live-Aktualisierung alle 2 Sekunden | Letzte Aktualisierung: ' + new Date().toLocaleTimeString('de-DE');
            document.getElementById('status').className = 'status';
        } catch (error) {
            document.getElementById('status').textContent = 'Fehler: ' + error.message;
            document.getElementById('status').className = 'status error';
        }
    }

    loadPlcData();
    setInterval(loadPlcData, 2000);
</script>
</body>
</html>