-- Starter-Schema fuer OPC UA -> MQTT -> Datenbank
-- Ziel: Speicherung von Snapshot-Daten, Statusmeldungen und MES-relevanten Werten

CREATE DATABASE IF NOT EXISTS datenkrake;
USE datenkrake;

CREATE TABLE IF NOT EXISTS stations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    station_name VARCHAR(100) NOT NULL UNIQUE,
    endpoint VARCHAR(100) NULL,
    source_file VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw_signals (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    station_id INT NOT NULL,
    signal_name VARCHAR(255) NOT NULL,
    signal_group VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NULL,
    value_string VARCHAR(1000) NULL,
    value_numeric DOUBLE NULL,
    value_bool BOOLEAN NULL,
    recorded_at TIMESTAMP NOT NULL,
    source_file VARCHAR(255) NULL,
    FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE,
    INDEX idx_raw_signals_station_time (station_id, recorded_at),
    INDEX idx_raw_signals_name (signal_name)
);

CREATE TABLE IF NOT EXISTS process_snapshots (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    station_id INT NOT NULL,
    recorded_at TIMESTAMP NOT NULL,
    heartbeat_json JSON NULL,
    process_io_json JSON NULL,
    mes_json JSON NULL,
    order_link_json JSON NULL,
    status_link_json JSON NULL,
    FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE,
    INDEX idx_process_snapshots_station_time (station_id, recorded_at)
);

CREATE TABLE IF NOT EXISTS events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    station_id INT NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_payload JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE,
    INDEX idx_events_station_time (station_id, created_at)
);

CREATE TABLE IF NOT EXISTS mes_records (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    station_id INT NOT NULL,
    recorded_at TIMESTAMP NOT NULL,
    order_id VARCHAR(100) NULL,
    product_id VARCHAR(100) NULL,
    error_code VARCHAR(100) NULL,
    fill_level DOUBLE NULL,
    cylinder_state VARCHAR(100) NULL,
    FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE,
    INDEX idx_mes_records_station_time (station_id, recorded_at)
);

-- Beispiel-Daten fuer die wichtigsten Stationen
INSERT INTO stations (station_name, endpoint, source_file)
VALUES
    ('leitstand', '192.168.36.1:4840', 'Leitstand.txt'),
    ('palettenlager1', '192.168.36.2:4840', 'Palettenlager1.txt'),
    ('rohlager', '192.168.36.3:4840', 'Rohlager Dosen.txt'),
    ('abfuellen', '192.168.36.4:4840', 'Abfüllen.txt'),
    ('qualitaet', '192.168.36.5:4840', 'Qualität Kamera.txt'),
    ('handling', '192.168.36.6:4840', 'Handling Saugarm.txt'),
    ('presse', '192.168.36.7:4840', 'Presse.txt'),
    ('palettenlager2', '192.168.36.8:4840', 'Palettenlager2.txt'),
    ('transfer_roboter', '192.168.36.9:4840', 'Transfersystem Roboter.txt'),
    ('transfer_hochregallager', '192.168.36.10:4840', 'Transfersystem Hochregallager.txt')
ON DUPLICATE KEY UPDATE station_name = station_name;
