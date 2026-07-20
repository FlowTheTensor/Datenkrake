"""
Gemeinsame Zugriffsschicht auf die Datenkrake-Telemetrie-DB fuer den
Agenten-Teil (Poller, DB-Agent, Orchestrator). Getrennt vom bestehenden
MCPLokalClaudDesktop/mcpserver.py, weil dieser Teil zusaetzlich SCHREIBEN
muss (audio_anomalien, wartungsereignisse) - dafuer der eigene, eng
begrenzte 'anomalie_writer'-User statt des rein lesenden 'mcp_read'.

Kennt weder MCP noch A2A noch LAP - reines Python.
"""
import os
import statistics
from contextlib import contextmanager

import pymysql

DB_HOST = os.environ.get("DK_DB_HOST", "datenkrake.local")
DB_PORT = int(os.environ.get("DK_DB_PORT", "3306"))
DB_NAME = os.environ.get("DK_DB_NAME", "telemetry")

READ_USER = os.environ.get("DK_READ_USER", "mcp_read")
READ_PASSWORD = os.environ.get("DK_READ_PASSWORD", "changeMeMcp")

WRITE_USER = os.environ.get("DK_WRITE_USER", "anomalie_writer")
WRITE_PASSWORD = os.environ.get("DK_WRITE_PASSWORD", "changeMeAnomalie")


@contextmanager
def _connection(user: str, password: str):
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=user,
        password=password,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
    )
    try:
        yield conn
    finally:
        conn.close()


def _read_connection():
    return _connection(READ_USER, READ_PASSWORD)


def _write_connection():
    return _connection(WRITE_USER, WRITE_PASSWORD)


# ---------------------------------------------------- Anomalieerkennung ---
def pruefe_akustik_anomalie(fenster: int = 20) -> dict:
    """Identische Heuristik wie in mcpserver.py (Mittelwert + Standard-
    abweichung auf peak_db) - bewusst dieselbe einfache Logik an beiden
    Stellen, damit MCP-Abfrage und automatischer Poller konsistent sind."""
    with _read_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, peak_db FROM audio_spectrum ORDER BY ts DESC LIMIT %s",
            (fenster,),
        )
        rows = cur.fetchall()[::-1]

    if len(rows) < 6:
        return {"anomalie": False, "grund": "zu wenige Datenpunkte"}

    referenz = [r["peak_db"] for r in rows[:-1]]
    aktuell = rows[-1]
    mittel = statistics.mean(referenz)
    std = statistics.pstdev(referenz) or 0.01
    anomalie = abs(aktuell["peak_db"] - mittel) > 2.5 * std

    return {
        "anomalie": anomalie,
        "bezug_id": aktuell["id"],
        "aktuell_peak_db": round(aktuell["peak_db"], 2),
        "referenz_mittel": round(mittel, 2),
        "referenz_std": round(std, 2),
    }


def anomalie_bereits_erfasst(bezug_id: int) -> bool:
    with _read_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM audio_anomalien WHERE bezug_id = %s", (bezug_id,))
        return cur.fetchone() is not None


def insert_anomalie(bezug_id: int, peak_db: float, mittel: float, std: float) -> int:
    with _write_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO audio_anomalien (bezug_id, peak_db, referenz_mittel, referenz_std) "
            "VALUES (%s, %s, %s, %s)",
            (bezug_id, peak_db, mittel, std),
        )
        conn.commit()
        return cur.lastrowid


def get_offene_anomalien() -> list[dict]:
    with _read_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, bezug_id, peak_db, referenz_mittel, erkannt_am "
            "FROM audio_anomalien WHERE erledigt = FALSE ORDER BY erkannt_am"
        )
        return cur.fetchall()


def markiere_anomalie_erledigt(anomalie_id: int) -> None:
    with _write_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE audio_anomalien SET erledigt = TRUE WHERE id = %s", (anomalie_id,)
        )
        conn.commit()


def log_wartungsereignis(anomalie_id: int, aktion: str, messwert: float) -> None:
    with _write_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO wartungsereignisse (anomalie_id, aktion, messwert) "
            "VALUES (%s, %s, %s)",
            (anomalie_id, aktion, messwert),
        )
        conn.commit()


def get_stats() -> list[dict]:
    with _read_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT label, COUNT(*) AS anzahl, ROUND(AVG(peak_db), 2) AS avg_peak_db
               FROM audio_spectrum GROUP BY label"""
        )
        return cur.fetchall()
