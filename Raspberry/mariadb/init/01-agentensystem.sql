-- Erweiterung des bestehenden Schemas (00-create-database.sql) um Tabellen
-- für das Agentensystem (siehe /Agentensystem/README.md).
--
-- Läuft bei einer NEUEN Installation automatisch mit (Docker führt alle
-- *.sql-Dateien in mariadb/init/ alphabetisch aus, sobald das data-Volume
-- leer ist). Bei einer BESTEHENDEN Installation einmalig manuell einspielen:
--   mysql -h <pi-ip> -P 3306 -u root -p telemetry < 01-agentensystem.sql

USE telemetry;

-- Ergebnisse des Anomalie-Pollers (siehe Agentensystem/anomalie_poller/).
-- bezug_id verweist auf den audio_spectrum-Eintrag, der den Ausschlag ausgeloest hat.
CREATE TABLE IF NOT EXISTS audio_anomalien (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    bezug_id BIGINT NOT NULL,
    peak_db REAL NOT NULL,
    referenz_mittel REAL NOT NULL,
    referenz_std REAL NOT NULL,
    erkannt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    erledigt BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_anomalie_spectrum FOREIGN KEY (bezug_id)
        REFERENCES audio_spectrum(id) ON DELETE CASCADE
);

-- Protokoll der vom Wartungs-Agent tatsaechlich ausgefuehrten LAP-Aktionen.
CREATE TABLE IF NOT EXISTS wartungsereignisse (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    anomalie_id BIGINT,
    aktion VARCHAR(30) NOT NULL,
    messwert REAL,
    ausgeloest_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_wartung_anomalie FOREIGN KEY (anomalie_id)
        REFERENCES audio_anomalien(id) ON DELETE SET NULL
);

-- Analog zum bestehenden mcp_read-User (nur lesend), aber mit
-- Schreibrechten auf genau die zwei neuen Tabellen - bewusst NICHT auf
-- audio_spectrum, das bleibt alleinige Domäne des bestehenden Subscribers.
CREATE USER IF NOT EXISTS 'anomalie_writer'@'%' IDENTIFIED BY 'changeMeAnomalie';
GRANT SELECT ON telemetry.audio_spectrum TO 'anomalie_writer'@'%';
GRANT SELECT, INSERT, UPDATE ON telemetry.audio_anomalien TO 'anomalie_writer'@'%';
GRANT SELECT, INSERT ON telemetry.wartungsereignisse TO 'anomalie_writer'@'%';

-- Der bestehende mcp_read-User braucht zusaetzlich Lesezugriff auf die
-- neuen Tabellen, damit sie ueber MCP abfragbar sind (schema://overview,
-- anomalien://offen).
GRANT SELECT ON telemetry.audio_anomalien TO 'mcp_read'@'%';
GRANT SELECT ON telemetry.wartungsereignisse TO 'mcp_read'@'%';

FLUSH PRIVILEGES;
