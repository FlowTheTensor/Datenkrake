<?php

require_once __DIR__ . '/../includes/db.php';

header('Content-Type: application/json; charset=utf-8');

try {
    $connection = database_connection();
    $action = $_GET['action'] ?? 'data';

    if ($action === 'data') {
        $result = $connection->query(
            'SELECT id, ts, station, endpoint, node_id, tag, datatype, wert_num, '
            . 'wert_bool, wert_text, payload_json, mqtt_topic, created_at '
            . 'FROM plc_telemetry ORDER BY ts DESC, id DESC LIMIT 1000'
        );

        $data = [];
        while ($row = $result->fetch_assoc()) {
            $data[] = $row;
        }

        echo json_encode(array_reverse($data));
    } elseif ($action === 'stats') {
        $stats = [];
        $result = $connection->query('SELECT COUNT(*) AS total FROM plc_telemetry');
        $stats['total'] = (int) $result->fetch_assoc()['total'];

        $result = $connection->query(
            'SELECT station, COUNT(*) AS count FROM plc_telemetry GROUP BY station ORDER BY station'
        );
        $stats['stations'] = [];
        while ($row = $result->fetch_assoc()) {
            $stats['stations'][] = [
                'station' => $row['station'],
                'count' => (int) $row['count'],
            ];
        }
        echo json_encode($stats);
    } elseif ($action === 'clear' && $_SERVER['REQUEST_METHOD'] === 'POST') {
        $result = $connection->query('SELECT COUNT(*) AS count FROM plc_telemetry');
        $count = (int) $result->fetch_assoc()['count'];
        $connection->query('TRUNCATE TABLE plc_telemetry');
        echo json_encode(['success' => true, 'deleted' => $count]);
    } else {
        http_response_code(404);
        echo json_encode(['error' => 'Unbekannte PLC-API-Aktion.']);
    }

    $connection->close();
} catch (Throwable $error) {
    http_response_code(500);
    echo json_encode(['error' => $error->getMessage()]);
}
