<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>PLC-Telemetrie Dashboard - Live</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
        .actions { margin-bottom: 15px; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
        .btn-danger { padding: 8px 20px; background: #dc3545; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }
        .btn-danger:hover { background: #c82333; }
        .btn-primary { padding: 8px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }
        .btn-primary:hover { background: #0069d9; }
        .import-group { display: flex; gap: 8px; align-items: center; }
        .import-status { font-size: 13px; color: #555; }

        .station-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
            gap: 16px;
            margin-top: 10px;
        }
        /* feste Kachelgröße */
        .station-card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 480px;
        }
        .station-card-header {
            background: #8b1a1a;
            color: white;
            padding: 10px 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
        }
        .station-card-header h2 { margin: 0; font-size: 15px; font-weight: 600; }
        .station-card-meta { font-size: 11px; opacity: 0.9; }
        .station-card-controls { display: flex; align-items: center; gap: 6px; font-size: 12px; }
        .station-card-controls select {
            border: none; border-radius: 4px; padding: 2px 6px; font-size: 12px;
            background: rgba(255,255,255,0.95); color: #333; max-width: 140px;
        }
        .station-chart-wrap {
            height: 160px;
            padding: 8px 10px 4px;
            border-bottom: 1px solid #eee;
            flex-shrink: 0;
            position: relative;
        }
        .station-chart-toolbar {
            display: flex;
            gap: 6px;
            align-items: center;
            margin-bottom: 4px;
            font-size: 12px;
        }
        .station-chart-toolbar select {
            flex: 1;
            min-width: 0;
            padding: 3px 6px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 12px;
        }
        .station-chart-canvas-wrap { height: 125px; }
        .station-card-body {
            padding: 0;
            overflow: auto;
            flex: 1;
            min-height: 0;
        }
        .station-card table { width: 100%; border-collapse: collapse; min-width: 0; }
        .station-card th, .station-card td {
            border: 1px solid #eee; padding: 5px 7px; font-size: 11px; text-align: left;
        }
        .station-card th { background: #f8f8f8; position: sticky; top: 0; }
        .station-card .empty { padding: 16px; color: #666; text-align: center; }

        @media (max-width: 600px) {
            .header { flex-direction: column; align-items: flex-start; }
            .logo { margin-left: 0; text-align: left; font-size: 22px; }
            .main-data-container { padding: 0 2px; }
            .station-card { height: 460px; }
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
        <div class="production-bar" style="background:#fff;padding:12px 14px;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,.1);margin-bottom:16px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;">
            <label for="serialSelect" style="font-weight:600;color:#8b1a1a;">Produktion / Seriennummer</label>
            <select id="serialSelect" style="padding:6px 10px;border:1px solid #ccc;border-radius:5px;min-width:220px;">
                <option value="">– Live (alle Daten) –</option>
            </select>
            <span id="serialMeta" style="font-size:13px;color:#555;"></span>
        </div>

        <div class="actions">
            <button class="btn-danger" type="button" onclick="clearPlcDatabase()">PLC-Daten löschen</button>
            <div class="import-group">
                <input type="file" id="csvImportInput" accept=".csv,text/csv">
                <button class="btn-primary" type="button" onclick="importPlcCsv()">CSV importieren</button>
            </div>
            <span class="import-status" id="importStatus"></span>
        </div>

        <div class="station-grid" id="stationGrid"></div>
    </div>

<script>
    const LIMIT_OPTIONS = [10, 25, 50, 100, 200];
    const DEFAULT_LIMIT = 25;
    const SERIES_LIMIT = 200;
    const limitsKey = 'plcStationLimits';
    const chartTagKey = 'plcStationChartTags';

    /** @type {Object.<string, Chart>} */
    const charts = {};
    let knownStations = [];
    let pauseRefresh = false;
    let selectedFrom = '';
    let selectedTo = '';
    let productionsCache = [];

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
        }[character]));
    }

    function safeId(station) {
        return String(station).replace(/[^a-zA-Z0-9_-]/g, '_');
    }

    function valueOf(row) {
        if (row.wert_num !== null && row.wert_num !== undefined && row.wert_num !== '') {
            return row.wert_num;
        }
        if (row.wert_bool !== null && row.wert_bool !== undefined && row.wert_bool !== '') {
            return (row.wert_bool == 1 || row.wert_bool === true || row.wert_bool === '1') ? 'true' : 'false';
        }
        return row.wert_text ?? '';
    }

    function numericValue(row) {
        if (row.wert_num !== null && row.wert_num !== undefined && row.wert_num !== '') {
            return Number(row.wert_num);
        }
        if (row.wert_bool !== null && row.wert_bool !== undefined && row.wert_bool !== '') {
            return (row.wert_bool == 1 || row.wert_bool === true || row.wert_bool === '1') ? 1 : 0;
        }
        return null;
    }

    function timeQuery() {
        let q = '';
        if (selectedFrom) q += '&from=' + encodeURIComponent(selectedFrom);
        if (selectedTo) q += '&to=' + encodeURIComponent(selectedTo);
        return q;
    }

    function loadLimits() {
        try { return JSON.parse(localStorage.getItem(limitsKey) || '{}') || {}; }
        catch (e) { return {}; }
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
        loadPlcData(true);
    }

    function loadChartTags() {
        try { return JSON.parse(localStorage.getItem(chartTagKey) || '{}') || {}; }
        catch (e) { return {}; }
    }
    function saveChartTag(station, tag) {
        const map = loadChartTags();
        map[station] = tag;
        localStorage.setItem(chartTagKey, JSON.stringify(map));
    }
    function getChartTag(station, availableTags) {
        const saved = loadChartTags()[station];
        if (saved && availableTags.includes(saved)) return saved;
        return availableTags.find(t => /F_?llstand|Fuellstand|Füllstand/i.test(t))
            || availableTags.find(t => /Seriennummer/i.test(t))
            || availableTags[0]
            || '';
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
            Object.keys(charts).forEach(k => { charts[k].destroy(); delete charts[k]; });
            knownStations = [];
            selectedFrom = '';
            selectedTo = '';
            document.getElementById('serialSelect').value = '';
            document.getElementById('serialMeta').textContent = '';
            loadPlcData(true);
        } catch (error) {
            alert('Fehler: ' + error.message);
        }
    }

    async function importPlcCsv() {
        const input = document.getElementById('csvImportInput');
        const statusEl = document.getElementById('importStatus');
        if (!input.files || !input.files.length) {
            alert('Bitte zuerst eine CSV-Datei auswählen.');
            return;
        }
        const formData = new FormData();
        formData.append('csv_file', input.files[0]);

        statusEl.textContent = 'Import läuft …';
        try {
            const response = await fetch('api/plc.php?action=import', { method: 'POST', body: formData });
            const data = await response.json();
            if (data.error) {
                alert('Fehler: ' + data.error);
                statusEl.textContent = '';
                return;
            }
            let message = `${data.inserted} Zeilen importiert, ${data.skipped} übersprungen.`;
            if (data.errors && data.errors.length) {
                message += '\n\nErste Fehler:\n' + data.errors.join('\n');
            }
            alert(message);
            statusEl.textContent = `Letzter Import: ${data.inserted} importiert, ${data.skipped} übersprungen.`;
            input.value = '';
            Object.keys(charts).forEach(k => { charts[k].destroy(); delete charts[k]; });
            knownStations = [];
            loadPlcData(true);
        } catch (error) {
            alert('Fehler: ' + error.message);
            statusEl.textContent = '';
        }
    }
    window.importPlcCsv = importPlcCsv;

    async function fetchStationData(station, limit) {
        const url = 'api/plc.php?action=data'
            + '&station=' + encodeURIComponent(station)
            + '&limit=' + encodeURIComponent(limit)
            + timeQuery();
        const response = await fetch(url);
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        return data;
    }

    async function fetchSeries(station, tag) {
        const url = 'api/plc.php?action=series'
            + '&station=' + encodeURIComponent(station)
            + '&tag=' + encodeURIComponent(tag)
            + '&limit=' + encodeURIComponent(SERIES_LIMIT)
            + timeQuery();
        const response = await fetch(url);
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        return data;
    }

    async function loadProductions() {
        const res = await fetch('api/plc.php?action=productions');
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        productionsCache = data.productions || [];

        const sel = document.getElementById('serialSelect');
        if (!sel) return;
        const previous = sel.value;
        sel.innerHTML = '<option value="">– Live (alle Daten) –</option>';
        productionsCache.forEach((p, idx) => {
            const label = p.open
                ? `${p.serial} · ab ${p.start} (läuft)`
                : `${p.serial} · ${p.start} → ${p.end}`;
            const opt = document.createElement('option');
            opt.value = String(idx);
            opt.textContent = label;
            sel.appendChild(opt);
        });
        if (previous !== '' && [...sel.options].some(o => o.value === previous)) {
            sel.value = previous;
        }
    }

    function onSerialChange() {
        const sel = document.getElementById('serialSelect');
        const meta = document.getElementById('serialMeta');
        const idx = sel.value;

        if (idx === '') {
            selectedFrom = '';
            selectedTo = '';
            meta.textContent = '';
        } else {
            const p = productionsCache[parseInt(idx, 10)];
            if (!p) return;
            selectedFrom = p.start || '';
            selectedTo = p.end || '';
            meta.textContent = p.open
                ? `Filter: ab ${p.start} (noch offen)`
                : `Filter: ${p.start} – ${p.end}`;
        }

        Object.keys(charts).forEach(k => { charts[k].destroy(); delete charts[k]; });
        knownStations = [];
        loadPlcData(true);
    }

    function upsertStemChart(station, canvas, labels, values) {
        if (charts[station]) {
            charts[station].data.labels = labels;
            charts[station].data.datasets[0].data = values;
            charts[station].update('none');
            return;
        }
        charts[station] = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: '#8b1a1a',
                    borderColor: '#8b1a1a',
                    borderWidth: 1,
                    barPercentage: 0.15,
                    categoryPercentage: 1.0,
                    maxBarThickness: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 6, font: { size: 9 } },
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { font: { size: 9 } },
                        grid: { color: 'rgba(0,0,0,0.06)' }
                    }
                }
            }
        });
    }

    async function loadStationChart(station, tag) {
        if (!tag) return;
        const canvas = document.getElementById('chart-canvas-' + safeId(station));
        if (!canvas) return;
        const rows = await fetchSeries(station, tag);
        const labels = rows.map(r => {
            const t = String(r.ts || '');
            return t.length > 19 ? t.slice(11, 19) : t;
        });
        const values = rows.map(r => numericValue(r));
        upsertStemChart(station, canvas, labels, values);
    }

    function onChartTagChange(station, selectEl) {
        const tag = selectEl.value;
        saveChartTag(station, tag);
        loadStationChart(station, tag).catch(console.error);
    }

    function bindPauseOnSelects(root) {
        root.querySelectorAll('select').forEach(sel => {
            sel.addEventListener('focus', () => { pauseRefresh = true; });
            sel.addEventListener('blur', () => {
                setTimeout(() => { pauseRefresh = false; }, 300);
            });
        });
    }

    function renderStationCard(station, totalCount, rows, limit, tags) {
        const list = (rows || []).slice().reverse();
        const sid = safeId(station);
        const selectedTag = getChartTag(station, tags);
        const tagOptions = tags.map(t =>
            `<option value="${escapeHtml(t)}" ${t === selectedTag ? 'selected' : ''}>${escapeHtml(t)}</option>`
        ).join('') || '<option value="">–</option>';

        const rowsHtml = list.length
            ? list.map(row => `
                <tr>
                    <td>${escapeHtml(row.ts)}</td>
                    <td>${escapeHtml(row.tag)}</td>
                    <td>${escapeHtml(row.datatype)}</td>
                    <td>${escapeHtml(valueOf(row))}</td>
                </tr>`).join('')
            : `<tr><td colspan="4" class="empty">Keine Daten</td></tr>`;

        const limitOptions = LIMIT_OPTIONS.map(n =>
            `<option value="${n}" ${n === limit ? 'selected' : ''}>${n}</option>`
        ).join('');

        return `
            <article class="station-card" data-station="${escapeHtml(station)}" id="card-${sid}">
                <header class="station-card-header">
                    <div>
                        <h2>${escapeHtml(station)}</h2>
                        <span class="station-card-meta" id="meta-${sid}">${totalCount} gesamt · Tabelle ${limit}</span>
                    </div>
                    <div class="station-card-controls">
                        <label>Limit</label>
                        <select data-station="${escapeHtml(station)}"
                            onchange="setLimit(this.dataset.station, parseInt(this.value, 10))">
                            ${limitOptions}
                        </select>
                    </div>
                </header>
                <div class="station-chart-wrap">
                    <div class="station-chart-toolbar">
                        <label>Variable</label>
                        <select id="tag-${sid}" data-station="${escapeHtml(station)}"
                            onchange="onChartTagChange(this.dataset.station, this)">
                            ${tagOptions}
                        </select>
                    </div>
                    <div class="station-chart-canvas-wrap">
                        <canvas id="chart-canvas-${sid}" data-station="${escapeHtml(station)}"></canvas>
                    </div>
                </div>
                <div class="station-card-body">
                    <table>
                        <thead>
                            <tr><th>Zeit</th><th>Tag</th><th>Typ</th><th>Wert</th></tr>
                        </thead>
                        <tbody id="tbody-${sid}">${rowsHtml}</tbody>
                    </table>
                </div>
            </article>
        `;
    }

    function updateStationCardInPlace(station, totalCount, rows, limit, tags) {
        const sid = safeId(station);
        const meta = document.getElementById('meta-' + sid);
        const tbody = document.getElementById('tbody-' + sid);
        if (!meta || !tbody) return false;

        meta.textContent = `${totalCount} gesamt · Tabelle ${limit}`;

        const list = (rows || []).slice().reverse();
        tbody.innerHTML = list.length
            ? list.map(row => `
                <tr>
                    <td>${escapeHtml(row.ts)}</td>
                    <td>${escapeHtml(row.tag)}</td>
                    <td>${escapeHtml(row.datatype)}</td>
                    <td>${escapeHtml(valueOf(row))}</td>
                </tr>`).join('')
            : `<tr><td colspan="4" class="empty">Keine Daten</td></tr>`;

        const tagSelect = document.getElementById('tag-' + sid);
        if (tagSelect && tags.length) {
            const current = tagSelect.value;
            const existing = new Set([...tagSelect.options].map(o => o.value));
            tags.forEach(t => {
                if (!existing.has(t)) {
                    const opt = document.createElement('option');
                    opt.value = t;
                    opt.textContent = t;
                    tagSelect.appendChild(opt);
                }
            });
            if (current) tagSelect.value = current;
        }
        return true;
    }

    function stationsEqual(a, b) {
        if (a.length !== b.length) return false;
        for (let i = 0; i < a.length; i++) {
            if (a[i] !== b[i]) return false;
        }
        return true;
    }

    /**
     * @param {boolean} forceRebuild
     */
    async function loadPlcData(forceRebuild = false) {
        if (pauseRefresh && !forceRebuild) return;

        try {
            await loadProductions();

            const statsResponse = await fetch('api/plc.php?action=stats' + timeQuery());
            const stats = await statsResponse.json();
            if (stats.error) throw new Error(stats.error);

            document.getElementById('total').textContent = stats.total || 0;
            const stations = (stats.stations || []).slice().sort((a, b) =>
                a.station.localeCompare(b.station, 'de')
            );
            document.getElementById('stations').textContent = stations.length;
            const tagsByStation = stats.tags_by_station || {};
            const stationNames = stations.map(s => s.station);
            const needRebuild = forceRebuild || !stationsEqual(stationNames, knownStations);

            const results = await Promise.all(
                stations.map(async item => {
                    const limit = getLimit(item.station);
                    const rows = await fetchStationData(item.station, limit);
                    const tags = tagsByStation[item.station] || [];
                    return { station: item.station, count: item.count, rows, limit, tags };
                })
            );

            const grid = document.getElementById('stationGrid');

            if (results.length === 0) {
                Object.keys(charts).forEach(k => { charts[k].destroy(); delete charts[k]; });
                knownStations = [];
                grid.innerHTML = '<div class="station-card"><div class="empty">Keine PLC-Daten vorhanden.</div></div>';
            } else if (needRebuild) {
                Object.keys(charts).forEach(k => { charts[k].destroy(); delete charts[k]; });
                grid.innerHTML = results
                    .map(r => renderStationCard(r.station, r.count, r.rows, r.limit, r.tags))
                    .join('');
                bindPauseOnSelects(grid);
                knownStations = stationNames;

                await Promise.all(results.map(r => {
                    const tag = getChartTag(r.station, r.tags);
                    return loadStationChart(r.station, tag);
                }));
            } else {
                await Promise.all(results.map(async r => {
                    updateStationCardInPlace(r.station, r.count, r.rows, r.limit, r.tags);
                    const tagSelect = document.getElementById('tag-' + safeId(r.station));
                    const tag = (tagSelect && tagSelect.value) || getChartTag(r.station, r.tags);
                    await loadStationChart(r.station, tag);
                }));
            }

            const mode = selectedFrom ? 'Produktion gefiltert' : 'Live-Aktualisierung alle 2 Sekunden';
            document.getElementById('status').textContent =
                mode + ' | Letzte Aktualisierung: ' + new Date().toLocaleTimeString('de-DE');
            document.getElementById('status').className = 'status';
        } catch (error) {
            document.getElementById('status').textContent = 'Fehler: ' + error.message;
            document.getElementById('status').className = 'status error';
        }
    }

    window.setLimit = setLimit;
    window.onChartTagChange = onChartTagChange;

    const serialSelect = document.getElementById('serialSelect');
    if (serialSelect) {
        serialSelect.addEventListener('change', onSerialChange);
        serialSelect.addEventListener('focus', () => { pauseRefresh = true; });
        serialSelect.addEventListener('blur', () => {
            setTimeout(() => { pauseRefresh = false; }, 300);
        });
    }

    loadPlcData(true);
    setInterval(() => {
        // Im Live-Modus alle 2 s; bei gewählter Seriennummer seltener
        if (!selectedFrom) {
            loadPlcData(false);
        }
    }, 2000);
</script>
</body>
</html>
