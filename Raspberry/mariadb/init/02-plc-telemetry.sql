-- PLC-Telemetrie aus Node-RED (MQTT-Topic plc/#).
-- Bei einer NEUEN Installation wird dieses Skript automatisch ausgefuehrt.
-- Bei einer BESTEHENDEN Installation einmalig manuell einspielen:
--   mysql -h <pi-ip> -P 3306 -u root -p telemetry < 02-plc-telemetry.sql

USE telemetry;

CREATE TABLE IF NOT EXISTS plc_telemetry (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ts DATETIME NOT NULL,
    station VARCHAR(80) NOT NULL,
    endpoint VARCHAR(80) NOT NULL,
    node_id VARCHAR(255) NOT NULL,
    tag VARCHAR(160) NOT NULL,
    datatype VARCHAR(40),
    wert_num DOUBLE NULL,
    wert_bool TINYINT(1) NULL,
    wert_text VARCHAR(255) NULL,
    payload_json JSON,
    mqtt_topic VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_plc_ts ON plc_telemetry(ts);
CREATE INDEX idx_plc_station_tag_ts ON plc_telemetry(station, tag, ts);
CREATE INDEX idx_plc_node_id_ts ON plc_telemetry(node_id, ts);

-- Der bestehende read-only MCP-User darf die neuen Messwerte lesen.
GRANT SELECT ON telemetry.plc_telemetry TO 'mcp_read'@'%';

FLUSH PRIVILEGES;
