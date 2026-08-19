<?php

require_once __DIR__ . '/../includes/db.php';

$table = $_GET['table'] ?? '';
$tables = [
    'audio_spectrum' => 'audio_daten.csv',
    'plc_telemetry' => 'plc_daten.csv',
];

if (!isset($tables[$table])) {
    http_response_code(400);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['error' => 'Ungültige Export-Tabelle.']);
    exit;
}

try {
    $connection = database_connection();
    $result = $connection->query("SELECT * FROM `{$table}` ORDER BY id ASC");

    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="' . $tables[$table] . '"');

    $output = fopen('php://output', 'w');
    $columns = [];
    while ($row = $result->fetch_assoc()) {
        if (!$columns) {
            $columns = array_keys($row);
            fputcsv($output, $columns, ';');
        }
        fputcsv($output, array_map(
            static fn ($value) => $value ?? '',
            array_values($row)
        ), ';');
    }

    if (!$columns) {
        $fields = $connection->query("SHOW COLUMNS FROM `{$table}`");
        while ($field = $fields->fetch_assoc()) {
            $columns[] = $field['Field'];
        }
        fputcsv($output, $columns, ';');
    }

    fclose($output);
    $connection->close();
} catch (Throwable $error) {
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['error' => $error->getMessage()]);
}