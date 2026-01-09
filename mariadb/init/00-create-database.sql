-- Initialization script for MariaDB.
-- Creates the measurements table for sensor data.

CREATE TABLE IF NOT EXISTS measurements (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ts DATETIME NOT NULL,
    sensor TEXT NOT NULL,
    ax REAL NOT NULL,
    ay REAL NOT NULL,
    az REAL NOT NULL,
    gx REAL NOT NULL,
    gy REAL NOT NULL,
    gz REAL NOT NULL,
    temperature REAL,
    anomaly_score REAL,
    anomaly_flag INTEGER DEFAULT 0
);