<?php

require_once __DIR__ . '/../includes/db.php';

header('Content-Type: application/json; charset=utf-8');

try {
    $connection = database_connection();
    $action = $_GET['action'] ?? 'data';

    if ($action === 'data') {
        $label = $_GET['label'] ?? null;
        if ($label === 'gut' || $label === 'schlecht') {
            $statement = $connection->prepare(
                'SELECT * FROM audio_spectrum WHERE label = ? ORDER BY ts DESC LIMIT 100'
            );
            $statement->bind_param('s', $label);
            $statement->execute();
            $result = $statement->get_result();
        } else {
            $result = $connection->query('SELECT * FROM audio_spectrum ORDER BY ts DESC LIMIT 100');
        }

        $data = [];
        while ($row = $result->fetch_assoc()) {
            $row['spectrum'] = json_decode($row['spectrum'], true);
            $data[] = $row;
        }

        echo json_encode(array_reverse($data));
    } elseif ($action === 'stats') {
        $stats = [];
        $result = $connection->query('SELECT label, COUNT(*) AS count FROM audio_spectrum GROUP BY label');
        while ($row = $result->fetch_assoc()) {
            $stats[$row['label']] = (int) $row['count'];
        }

        $result = $connection->query('SELECT COUNT(*) AS total FROM audio_spectrum');
        $stats['total'] = (int) $result->fetch_assoc()['total'];
        echo json_encode($stats);
    } elseif ($action === 'clear' && $_SERVER['REQUEST_METHOD'] === 'POST') {
        $result = $connection->query('SELECT COUNT(*) AS count FROM audio_spectrum');
        $count = (int) $result->fetch_assoc()['count'];
        $connection->query('TRUNCATE TABLE audio_spectrum');
        echo json_encode(['success' => true, 'deleted' => $count]);
    } else {
        http_response_code(404);
        echo json_encode(['error' => 'Unbekannte Audio-API-Aktion.']);
    }

    $connection->close();
} catch (Throwable $error) {
    http_response_code(500);
    echo json_encode(['error' => $error->getMessage()]);
}