<?php

function database_connection(): mysqli
{
    $connection = new mysqli('db', 'sensor', 'changeMeSensor', 'telemetry');
    if ($connection->connect_error) {
        throw new RuntimeException($connection->connect_error);
    }

    $connection->set_charset('utf8mb4');
    return $connection;
}