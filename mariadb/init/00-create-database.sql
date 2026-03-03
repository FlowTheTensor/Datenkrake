-- Initialization script for MariaDB.
-- Creates the audio_spectrum table for audio spectrum data.

CREATE TABLE IF NOT EXISTS audio_spectrum (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ts DATETIME NOT NULL,
    label VARCHAR(20) NOT NULL DEFAULT 'gut',
    peak_freq REAL NOT NULL,
    peak_db REAL NOT NULL,
    spectrum JSON,
    sample_rate INT DEFAULT 16000
);

-- Index für schnelle Abfragen nach Label und Zeit
CREATE INDEX idx_label ON audio_spectrum(label);
CREATE INDEX idx_ts ON audio_spectrum(ts);

-- Read-only user for MCP server access.
CREATE USER IF NOT EXISTS 'mcp_read'@'%' IDENTIFIED BY 'changeMeMcp';
GRANT SELECT ON telemetry.* TO 'mcp_read'@'%';
FLUSH PRIVILEGES;