<?php

require_once __DIR__ . '/../includes/db.php';

header('Content-Type: application/json; charset=utf-8');

try {
    $connection = database_connection();
    $action = $_GET['action'] ?? 'data';

    if ($action === 'data') {
        $station = isset($_GET['station']) ? trim((string) $_GET['station']) : '';
        $limit = (int) ($_GET['limit'] ?? 50);
        if ($limit < 1) {
            $limit = 1;
        }
        if ($limit > 500) {
            $limit = 500;
        }

        if ($station !== '') {
            $sql = 'SELECT id, ts, station, endpoint, node_id, tag, datatype, wert_num, '
                . 'wert_bool, wert_text, payload_json, mqtt_topic, created_at '
                . 'FROM plc_telemetry WHERE station = ? '
                . 'ORDER BY ts DESC, id DESC LIMIT ' . $limit;
            $statement = $connection->prepare($sql);
            if ($statement === false) {
                throw new RuntimeException('Prepare failed: ' . $connection->error);
            }
            $statement->bind_param('s', $station);
            if (!$statement->execute()) {
                throw new RuntimeException('Execute failed: ' . $statement->error);
            }
            $result = $statement->get_result();
            if ($result === false) {
                throw new RuntimeException('get_result failed (mysqlnd?).');
            }
        } else {
            $sql = 'SELECT id, ts, station, endpoint, node_id, tag, datatype, wert_num, '
                . 'wert_bool, wert_text, payload_json, mqtt_topic, created_at '
                . 'FROM plc_telemetry ORDER BY ts DESC, id DESC LIMIT ' . $limit;
            $result = $connection->query($sql);
            if ($result === false) {
                throw new RuntimeException('Query failed: ' . $connection->error);
            }
        }

        $data = [];
        while ($row = $result->fetch_assoc()) {
            $data[] = $row;
        }

        echo json_encode(array_reverse($data));
    } elseif ($action === 'stats') {
        $stats = ['total' => 0, 'stations' => []];

        $result = $connection->query('SELECT COUNT(*) AS total FROM plc_telemetry');
        if ($result === false) {
            throw new RuntimeException($connection->error);
        }
        $stats['total'] = (int) $result->fetch_assoc()['total'];

        $result = $connection->query(
            'SELECT station, COUNT(*) AS count FROM plc_telemetry GROUP BY station ORDER BY station'
        );
        if ($result === false) {
            throw new RuntimeException($connection->error);
        }
        while ($row = $result->fetch_assoc()) {
            $stats['stations'][] = [
                'station' => $row['station'],
                'count' => (int) $row['count'],
            ];
        }

        echo json_encode($stats);
    } elseif ($action === 'clear' && $_SERVER['REQUEST_METHOD'] === 'POST') {
        $result = $connection->query('SELECT COUNT(*) AS count FROM plc_telemetry');
        if ($result === false) {
            throw new RuntimeException($connection->error);
        }
        $count = (int) $result->fetch_assoc()['count'];
        if (!$connection->query('TRUNCATE TABLE plc_telemetry')) {
            throw new RuntimeException($connection->error);
        }
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
