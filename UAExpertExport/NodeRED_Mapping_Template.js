// Node-RED Function-Node Template für OPC UA -> MQTT -> Datenbank
// Eingabe: msg.payload enthält die Werte einer Station (z. B. aus OPC UA / MQTT-In)
// Ausgabe: mehrere MQTT-Nachrichten fuer heartbeat, process_io, mes, order_link und status_link

function getValue(obj, keys, fallback) {
    for (const key of keys) {
        if (obj && Object.prototype.hasOwnProperty.call(obj, key) && obj[key] !== undefined && obj[key] !== null) {
            return obj[key];
        }
    }
    return fallback;
}

const station = msg.station || msg.payload?.station || 'station';
const ts = new Date().toISOString();

const heartbeat = {
    station,
    timestamp: ts,
    operating_mode: getValue(msg.payload, ['OperatingMode', 'operating_mode'], null),
    online: getValue(msg.payload, ['Status_Online', 'online'], null)
};

const process_io = {
    station,
    timestamp: ts,
    inputs: {},
    outputs: {}
};

// Beispiel: Diese Felder koennen je nach Export-Datei erweitert werden.
const processKeys = [
    'OperatingMode',
    'Status_Online',
    'Status_Trigger_ready',
    'Status_Data_valid',
    'Status_Error',
    'Command_Code',
    'Command_Argument',
    'Result_Command_Code',
    'Return_Command_Code',
    'WaageGS',
    'WaageAS',
    'AnalogInduktiv'
];

for (const key of processKeys) {
    if (Object.prototype.hasOwnProperty.call(msg.payload || {}, key)) {
        process_io.inputs[key] = msg.payload[key];
    }
}

const mes = {
    station,
    timestamp: ts,
    order_id: getValue(msg.payload, ['Auftragsnummer', 'OrderId', 'order_id'], null),
    product_id: getValue(msg.payload, ['Produkt', 'ProductId', 'product_id'], null),
    error_code: getValue(msg.payload, ['Fehler', 'ErrorCode', 'error_code'], null),
    fill_level: getValue(msg.payload, ['Fuellstand', 'FillLevel', 'fill_level'], null),
    cylinder_state: getValue(msg.payload, ['MesZylinder', 'CylinderState', 'cylinder_state'], null)
};

const order_link = {
    station,
    timestamp: ts,
    order: getValue(msg.payload, ['uvlaVonLeitstandAuftrag', 'order'], null)
};

const status_link = {
    station,
    timestamp: ts,
    status: getValue(msg.payload, ['uzlsZuLeitstandStatus', 'status'], null)
};

return [
    { topic: `fabrik/linie1/${station}/heartbeat`, payload: heartbeat },
    { topic: `fabrik/linie1/${station}/process_io`, payload: process_io },
    { topic: `fabrik/linie1/${station}/mes`, payload: mes },
    { topic: `fabrik/linie1/${station}/order_link`, payload: order_link },
    { topic: `fabrik/linie1/${station}/status_link`, payload: status_link }
];
