<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>PLC-Telemetrie - Datenkrake</title>
    <style>
        :root { color-scheme: light; font-family: Arial, sans-serif; }
        body { margin: 0; padding: 24px; background: #f4f6f8; color: #222; }
        main { max-width: 1200px; margin: 0 auto; }
        header { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
        h1 { color: #164a63; margin: 0; }
        nav a { color: #164a63; margin-right: 14px; }
        .status { padding: 10px 12px; margin: 18px 0; border-radius: 4px; background: #d9edf7; color: #164a63; }
        .status.error { background: #f8d7da; color: #721c24; }
        .stats { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 18px; }
        .stat { background: white; border-left: 4px solid #164a63; padding: 14px 20px; min-width: 140px; box-shadow: 0 2px 4px rgba(0,0,0,.08); }
        .stat strong { display: block; font-size: 28px; }
        .panel { background: white; padding: 16px; box-shadow: 0 2px 4px rgba(0,0,0,.08); overflow: auto; }
        table { border-collapse: collapse; width: 100%; min-width: 900px; }
        th, td { border: 1px solid #d8dde1; padding: 8px; text-align: left; font-size: 13px; vertical-align: top; }
        th { background: #eef2f4; position: sticky; top: 0; }
        code { white-space: pre-wrap; word-break: break-word; }
        @media (max-width: 600px) { body { padding: 14px; } }
    </style>
</head>
<body>
<main>
    <header>
        <h1>PLC-Telemetrie</h1>
        <nav><a href="index.html">Leitstand</a><a href="audiodaten.php">Audio-Daten</a></nav>
    </header>
    <div class="status" id="status">Lade PLC-Daten ...</div>
    <div class="stats">
        <div class="stat"><strong id="total">0</strong>Messwerte</div>
        <div class="stat"><strong id="stations">0</strong>Stationen</div>
    </div>
    <section class="panel">
        <table>
            <thead>
                <tr><th>Zeit</th><th>Station</th><th>Endpoint</th><th>Tag</th><th>Datentyp</th><th>Wert</th><th>MQTT-Topic</th></tr>
            </thead>
            <tbody id="data"></tbody>
        </table>
    </section>
</main>
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