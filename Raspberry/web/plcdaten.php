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
        .header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 10px; flex-wrap: wrap; }
        .logo { font-family: 'Times New Roman', serif; font-size: 28px; font-weight: normal; color: #333; letter-spacing: 1px; margin-left: 20px; text-align: right; line-height: 1.1; }
        .logo .red-dot { color: #c00; }
        .logo-underline { display: inline-block; border-bottom: 2px solid #333; padding-bottom: 2px; }
        .logo-underline-red { display: inline-block; border-bottom: 2px solid #c00; padding-bottom: 2px; }
        .page-nav { margin-bottom: 15px; }
        .page-nav a { color: #8b1a1a; font-size: 13px; margin-right: 15px; }
        .main-data-container { max-width: 1100px; margin: 0 auto; width: 100%; }
        .actions { margin-bottom: 15px; }
        .btn-danger { padding: 8px 20px; background: #dc3545; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }
        .btn-danger:hover { background: #c82333; }
        .station-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 16px;
            margin-top: 10px;
        }
        .station-card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            max-height: 420px;
        }
        .station-card-header {
            background: #8b1a1a;
            color: white;
            padding: 12px 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
        }
        .station-card-header h2 { margin: 0; font-size: 16px; font-weight: 600; }
        .station-card-meta { font-size: 12px; opacity: 0.9; }
        .station-card-controls { display: flex; align-items: center; gap: 6px; font-size: 12px; }
        .station-card-controls select {
            border: none; border-radius: 4px; padding: 2px 6px; font-size: 12px;
            background: rgba(255,255,255,0.95); color: #333;
        }
        .station-card-body { padding: 0; overflow: auto; flex: 1; }
        .station-card table { width: 100%; border-collapse: collapse; min-width: 0; }
        .station-card th, .station-card td {
            border: 1px solid #eee; padding: 6px 8px; font-size: 12px; text-align: left;
        }
        .station-card th { background: #f8f8f8; position: sticky; top: 0; }
        .station-card .empty { padding: 20px; color: #666; text-align: center; }
        @media (max-width: 600px) {
            .header { flex-direction: column; align-items: flex-start; }
            .logo { margin-left: 0; text-align: left; font-size: 22px; }
            .main-data-container { padding: 0 2px; }
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

        <div class="actions">
            <button class="btn-danger" type="button" onclick="clearPlcDatabase()">PLC-Daten löschen</button>
        </div>

        <div class="station-grid" id="stationGrid"></div>
    </div>

<script>
    const LIMIT_OPTIONS = [10, 25, 50, 100, 200];
    const DEFAULT_LIMIT = 25;
    const limitsKey = 'plcStationLimits';

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
        }[character]));
    }

    function valueOf(row) {
        if (row.wert_num !== null && row.wert_num !== undefined) return row.wert_num;
        if (row.wert_bool !== null && row.wert_bool !== undefined) return row.wert_bool ? 'true' : 'false';
        return row.wert_text ?? '';
    }

    function loadLimits() {
        try {
            return JSON.parse(localStorage.getItem(limitsKey) || '{}') || {};
        } catch (e) {
            return {};
        }
    }

    function saveLimits(limits) {
        localStorage.setItem(limitsKey, JSON.stringify(limits));
    }

    function getLimit(station) {
        const value = parseInt(loadLimits()[station], 10);
        return LIMIT_OPTIONS.includes(value) ? value : DEFAULT_LIMIT;
    }

    function setLimit(station, limit) {
        const limits = loadLimits();
        limits[station] = limit;
        saveLimits(limits);
        loadPlcData();
    }

    async function clearPlcDatabase() {
        if (!confirm('Wirklich ALLE PLC-Daten aus der Datenbank löschen? Das kann nicht rückgängig gemacht werden!')) {
            return;
        }
        try {
            const response = await fetch('api/plc.php?action=clear', { method: 'POST' });
            const data = await response.json();
            if (data.error) {
                alert('Fehler: ' + data.error);
                return;
            }
            alert((data.deleted ?? 0) + ' Einträge gelöscht.');
            loadPlcData();
        } catch (error) {
            alert('Fehler: ' + error.message);
        }
    }

    function limitSelectHtml(station, current) {
        const safeStation = escapeHtml(station).replace(/'/g, '&#039;');
        const options = LIMIT_OPTIONS.map(n =>
            `<option value="${n}" ${n === current ? 'selected' : ''}>${n}</option>`
        ).join('');
        return `
            <div class="station-card-controls">
                <label>Limit</label>
                <select onchange="setLimit(this.dataset.station, parseInt(this.value, 10))" data-station="${safeStation}">
                    ${options}
                </select>
            </div>
        `;
    }

    function renderStationCard(station, totalCount, rows, limit) {
        const list = (rows || []).slice().reverse();
        const rowsHtml = list.length
            ? list.map(row => `
                <tr>
                    <td>${escapeHtml(row.ts)}</td>
                    <td>${escapeHtml(row.tag)}</td>
                    <td>${escapeHtml(row.datatype)}</td>
                    <td>${escapeHtml(valueOf(row))}</td>
                </tr>
              `).join('')
            : `<tr><td colspan="4" class="empty">Keine Daten</td></tr>`;

        return `
            <article class="station-card">
                <header class="station-card-header">
                    <div>
                        <h2>${escapeHtml(station)}</h2>
                        <span class="station-card-meta">${totalCount} gesamt · letzte ${limit}</span>
                    </div>
                    ${limitSelectHtml(station, limit)}
                </header>
                <div class="station-card-body">
                    <table>
                        <thead>
                            <tr><th>Zeit</th><th>Tag</th><th>Typ</th><th>Wert</th></tr>
                        </thead>
                        <tbody>${rowsHtml}</tbody>
                    </table>
                </div>
            </article>
        `;
    }

    async function fetchStationData(station, limit) {
        const url = 'api/plc.php?action=data'
            + '&station=' + encodeURIComponent(station)
            + '&limit=' + encodeURIComponent(limit);
        const response = await fetch(url);
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        return data;
    }

    async function loadPlcData() {
        try {
            const statsResponse = await fetch('api/plc.php?action=stats');
            const stats = await statsResponse.json();
            if (stats.error) throw new Error(stats.error);

            document.getElementById('total').textContent = stats.total || 0;
            const stations = stats.stations || [];
            document.getElementById('stations').textContent = stations.length;

            const results = await Promise.all(
                stations.map(async item => {
                    const limit = getLimit(item.station);
                    const rows = await fetchStationData(item.station, limit);
                    return { station: item.station, count: item.count, rows, limit };
                })
            );

            const grid = document.getElementById('stationGrid');
            if (results.length === 0) {
                grid.innerHTML = '<div class="station-card"><div class="empty">Keine PLC-Daten vorhanden.</div></div>';
            } else {
                grid.innerHTML = results
                    .sort((a, b) => a.station.localeCompare(b.station, 'de'))
                    .map(r => renderStationCard(r.station, r.count, r.rows, r.limit))
                    .join('');
            }

            document.getElementById('status').textContent =
                'Live-Aktualisierung alle 2 Sekunden | Letzte Aktualisierung: ' +
                new Date().toLocaleTimeString('de-DE');
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
