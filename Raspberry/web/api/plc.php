<?php

require_once __DIR__ . '/../includes/db.php';

header('Content-Type: application/json; charset=utf-8');

function clamp_limit(int $limit, int $min, int $max): int
{
    if ($limit < $min) {
        return $min;
    }
    if ($limit > $max) {
        return $max;
    }
    return $limit;
}

try {
    $connection = database_connection();
    $action = $_GET['action'] ?? 'data';

    if ($action === 'data') {
        $station = isset($_GET['station']) ? trim((string) $_GET['station']) : '';
        $from = isset($_GET['from']) ? trim((string) $_GET['from']) : '';
        $to = isset($_GET['to']) ? trim((string) $_GET['to']) : '';
        $limit = clamp_limit((int) ($_GET['limit'] ?? 50), 1, 2000);

        $sql = 'SELECT id, ts, station, endpoint, node_id, tag, datatype, wert_num, '
            . 'wert_bool, wert_text, payload_json, mqtt_topic, created_at '
            . 'FROM plc_telemetry WHERE 1=1';
        $types = '';
        $params = [];

        if ($station !== '') {
            $sql .= ' AND station = ?';
            $types .= 's';
            $params[] = $station;
        }
        if ($from !== '') {
            $sql .= ' AND ts >= ?';
            $types .= 's';
            $params[] = $from;
        }
        if ($to !== '') {
            $sql .= ' AND ts <= ?';
            $types .= 's';
            $params[] = $to;
        }

        $sql .= ' ORDER BY ts DESC, id DESC LIMIT ' . $limit;

        if ($types !== '') {
            $statement = $connection->prepare($sql);
            if ($statement === false) {
                throw new RuntimeException('Prepare failed: ' . $connection->error);
            }
            $statement->bind_param($types, ...$params);
            if (!$statement->execute()) {
                throw new RuntimeException('Execute failed: ' . $statement->error);
            }
            $result = $statement->get_result();
        } else {
            $result = $connection->query($sql);
        }
        if ($result === false) {
            throw new RuntimeException($connection->error);
        }

        $data = [];
        while ($row = $result->fetch_assoc()) {
            $data[] = $row;
        }
        echo json_encode(array_reverse($data));

    } elseif ($action === 'stats') {
        $stats = ['total' => 0, 'stations' => [], 'tags' => [], 'tags_by_station' => []];
        $from = isset($_GET['from']) ? trim((string) $_GET['from']) : '';
        $to = isset($_GET['to']) ? trim((string) $_GET['to']) : '';

        $where = ' WHERE 1=1';
        $types = '';
        $params = [];
        if ($from !== '') {
            $where .= ' AND ts >= ?';
            $types .= 's';
            $params[] = $from;
        }
        if ($to !== '') {
            $where .= ' AND ts <= ?';
            $types .= 's';
            $params[] = $to;
        }

        $run = function (string $sql) use ($connection, $types, $params) {
            if ($types !== '') {
                $st = $connection->prepare($sql);
                if ($st === false) {
                    throw new RuntimeException($connection->error);
                }
                $st->bind_param($types, ...$params);
                $st->execute();
                return $st->get_result();
            }
            $r = $connection->query($sql);
            if ($r === false) {
                throw new RuntimeException($connection->error);
            }
            return $r;
        };

        $result = $run('SELECT COUNT(*) AS total FROM plc_telemetry' . $where);
        $stats['total'] = (int) $result->fetch_assoc()['total'];

        $result = $run(
            'SELECT station, COUNT(*) AS count FROM plc_telemetry' . $where
            . ' GROUP BY station ORDER BY station'
        );
        while ($row = $result->fetch_assoc()) {
            $stats['stations'][] = [
                'station' => $row['station'],
                'count' => (int) $row['count'],
            ];
        }

        $result = $run(
            'SELECT DISTINCT tag FROM plc_telemetry' . $where . ' ORDER BY tag'
        );
        while ($row = $result->fetch_assoc()) {
            $stats['tags'][] = $row['tag'];
        }

        $result = $run(
            'SELECT station, tag FROM plc_telemetry' . $where
            . ' GROUP BY station, tag ORDER BY station, tag'
        );
        while ($row = $result->fetch_assoc()) {
            $st = $row['station'];
            if (!isset($stats['tags_by_station'][$st])) {
                $stats['tags_by_station'][$st] = [];
            }
            $stats['tags_by_station'][$st][] = $row['tag'];
        }

        echo json_encode($stats);

    } elseif ($action === 'series') {
        $station = isset($_GET['station']) ? trim((string) $_GET['station']) : '';
        $tag = isset($_GET['tag']) ? trim((string) $_GET['tag']) : '';
        $from = isset($_GET['from']) ? trim((string) $_GET['from']) : '';
        $to = isset($_GET['to']) ? trim((string) $_GET['to']) : '';
        $limit = clamp_limit((int) ($_GET['limit'] ?? 200), 1, 2000);

        $sql = 'SELECT ts, station, tag, datatype, wert_num, wert_bool, wert_text '
            . 'FROM plc_telemetry WHERE 1=1';
        $types = '';
        $params = [];

        if ($station !== '') {
            $sql .= ' AND station = ?';
            $types .= 's';
            $params[] = $station;
        }
        if ($tag !== '') {
            $sql .= ' AND tag = ?';
            $types .= 's';
            $params[] = $tag;
        }
        if ($from !== '') {
            $sql .= ' AND ts >= ?';
            $types .= 's';
            $params[] = $from;
        }
        if ($to !== '') {
            $sql .= ' AND ts <= ?';
            $types .= 's';
            $params[] = $to;
        }

        $sql .= ' ORDER BY ts DESC, id DESC LIMIT ' . $limit;

        if ($types !== '') {
            $statement = $connection->prepare($sql);
            if ($statement === false) {
                throw new RuntimeException('Prepare failed: ' . $connection->error);
            }
            $statement->bind_param($types, ...$params);
            if (!$statement->execute()) {
                throw new RuntimeException('Execute failed: ' . $statement->error);
            }
            $result = $statement->get_result();
        } else {
            $result = $connection->query($sql);
        }
        if ($result === false) {
            throw new RuntimeException($connection->error);
        }

        $rows = [];
        while ($row = $result->fetch_assoc()) {
            $rows[] = $row;
        }
        echo json_encode(array_reverse($rows));

    } elseif ($action === 'productions') {
        // Chronologisch: Seriennummer > 0 = Start, danach 0 = Ende
        $result = $connection->query(
            "SELECT ts, wert_num FROM plc_telemetry "
            . "WHERE station = 'leitstand' AND tag = 'dbHMI_uiSeriennummer' "
            . "ORDER BY ts ASC, id ASC"
        );
        if ($result === false) {
            throw new RuntimeException($connection->error);
        }

        $productions = [];
        $current = null;

        while ($row = $result->fetch_assoc()) {
            $value = $row['wert_num'];
            if ($value === null || $value === '') {
                continue;
            }
            $num = (int) $value;

            if ($num > 0) {
                // offene Produktion abschließen, falls unsauber
                if ($current !== null && empty($current['end'])) {
                    $current['end'] = $row['ts'];
                    $current['open'] = false;
                }
                $current = [
                    'serial' => $num,
                    'start' => $row['ts'],
                    'end' => null,
                    'open' => true,
                ];
                $productions[] = $current;
            } elseif ($num === 0 && $current !== null && empty($current['end'])) {
                $current['end'] = $row['ts'];
                $current['open'] = false;
                $current = null;
            }
        }

        // neueste zuerst
        $productions = array_reverse($productions);
        echo json_encode(['productions' => $productions]);

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
