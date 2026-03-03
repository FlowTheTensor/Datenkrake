#!/usr/bin/env python3
"""
MCP-Server fuer Claude Desktop - Zugriff auf die Datenkrake MariaDB.
Verbindet sich mit datenkrake.local und stellt die audio_spectrum Tabelle zur Verfuegung.
Nur lesender Zugriff ueber den mcp_read User.
"""

import json
import pymysql
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# --- Konfiguration ---
DB_HOST = "datenkrake.local"
DB_PORT = 3306
DB_USER = "mcp_read"
DB_PASSWORD = "changeMeMcp"
DB_NAME = "telemetry"

mcp = FastMCP("Datenkrake MariaDB")


def get_connection():
    """Oeffnet eine Datenbankverbindung."""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
    )


@mcp.tool()
def get_recent(limit: int = 20) -> str:
    """
    Gibt die neuesten Eintraege aus der audio_spectrum Tabelle zurueck.

    Args:
        limit: Anzahl der Eintraege (Standard: 20, max: 500)
    """
    limit = min(max(1, limit), 500)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, ts, label, peak_freq, peak_db, sample_rate "
                "FROM audio_spectrum ORDER BY ts DESC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()
        for row in rows:
            if isinstance(row.get("ts"), datetime):
                row["ts"] = row["ts"].isoformat()
        return json.dumps(rows, ensure_ascii=False, indent=2)
    finally:
        conn.close()


@mcp.tool()
def get_stats() -> str:
    """
    Gibt Statistiken der gespeicherten Audio-Spektrum-Daten zurueck:
    Anzahl Eintraege pro Label, Durchschnitte und Zeitraum.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    label,
                    COUNT(*)           AS anzahl,
                    ROUND(AVG(peak_freq), 2) AS avg_peak_freq_hz,
                    ROUND(AVG(peak_db),   2) AS avg_peak_db,
                    MIN(ts)            AS aeltester_eintrag,
                    MAX(ts)            AS neuester_eintrag
                FROM audio_spectrum
                GROUP BY label
                ORDER BY anzahl DESC
                """
            )
            rows = cur.fetchall()
        for row in rows:
            for key in ("aeltester_eintrag", "neuester_eintrag"):
                if isinstance(row.get(key), datetime):
                    row[key] = row[key].isoformat()
        return json.dumps(rows, ensure_ascii=False, indent=2)
    finally:
        conn.close()


@mcp.tool()
def get_spectrum(record_id: int) -> str:
    """
    Gibt den vollstaendigen Datensatz inkl. FFT-Spektrum-Array fuer eine bestimmte ID zurueck.

    Args:
        record_id: Die ID des Datensatzes in audio_spectrum
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM audio_spectrum WHERE id = %s",
                (record_id,),
            )
            row = cur.fetchone()
        if row is None:
            return json.dumps({"fehler": f"Kein Datensatz mit ID {record_id} gefunden."})
        if isinstance(row.get("ts"), datetime):
            row["ts"] = row["ts"].isoformat()
        if isinstance(row.get("spectrum"), str):
            row["spectrum"] = json.loads(row["spectrum"])
        return json.dumps(row, ensure_ascii=False, indent=2)
    finally:
        conn.close()


@mcp.tool()
def query(sql: str) -> str:
    """
    Fuehrt eine beliebige SELECT-Abfrage auf der Datenkrake-Datenbank aus.
    Nur SELECT-Anweisungen sind erlaubt (kein INSERT/UPDATE/DELETE).

    Args:
        sql: Die SQL SELECT-Abfrage
    """
    sql_stripped = sql.strip().upper()
    if not sql_stripped.startswith("SELECT") and not sql_stripped.startswith("SHOW") and not sql_stripped.startswith("DESCRIBE"):
        return json.dumps({"fehler": "Nur SELECT-, SHOW- und DESCRIBE-Abfragen sind erlaubt."})
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchmany(1000)  # max 1000 Zeilen
        for row in rows:
            for key, val in row.items():
                if isinstance(val, datetime):
                    row[key] = val.isoformat()
        return json.dumps(rows, ensure_ascii=False, indent=2)
    except pymysql.Error as e:
        return json.dumps({"fehler": str(e)})
    finally:
        conn.close()


@mcp.tool()
def get_table_info() -> str:
    """
    Gibt die Tabellenstruktur (DESCRIBE) der audio_spectrum Tabelle zurueck.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DESCRIBE audio_spectrum")
            rows = cur.fetchall()
        return json.dumps(rows, ensure_ascii=False, indent=2)
    finally:
        conn.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")
