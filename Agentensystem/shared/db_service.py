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
from datetime import timedelta

import pymysql
from influxdb_client import InfluxDBClient

DB_HOST = os.environ.get("DK_DB_HOST", "datenkrake.local")
DB_PORT = int(os.environ.get("DK_DB_PORT", "3306"))
DB_NAME = os.environ.get("DK_DB_NAME", "telemetry")

READ_USER = os.environ.get("DK_READ_USER", "mcp_read")
READ_PASSWORD = os.environ.get("DK_READ_PASSWORD", "changeMeMcp")

WRITE_USER = os.environ.get("DK_WRITE_USER", "anomalie_writer")
WRITE_PASSWORD = os.environ.get("DK_WRITE_PASSWORD", "changeMeAnomalie")

INFLUX_URL = os.environ.get("DK_INFLUX_URL", "http://datenkrake.local:8086")
INFLUX_TOKEN = os.environ.get("DK_INFLUX_TOKEN", "changeMeHistorianToken")
INFLUX_ORG = os.environ.get("DK_INFLUX_ORG", "datenkrake")
INFLUX_BUCKET = os.environ.get("DK_INFLUX_BUCKET", "telemetrie")


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


def pruefe_akustik_anomalie_influx(fenster: int = 20) -> dict:
    """Influx-Variante derselben Heuristik (Mittelwert + Standardabweichung
    auf peak_db). Liefert absichtlich noch keine bezug_id, weil diese im
    operativen System aus MariaDB stammt und dort als FK gebraucht wird."""
    # Fuer kleine Fenster etwas Puffer holen, falls einzelne Punkte fehlen.
    limit = max(fenster + 5, 30)
    # Fenster grob auf Zeit abbilden: bei typischen Raten reichen 24h gut aus.
    lookback = timedelta(hours=24)
    flux = (
        f'from(bucket: "{INFLUX_BUCKET}")\n'
        f'  |> range(start: -{int(lookback.total_seconds())}s)\n'
        '  |> filter(fn: (r) => r["_measurement"] == "audio_spectrum")\n'
        '  |> filter(fn: (r) => r["_field"] == "peak_db")\n'
        '  |> keep(columns: ["_time", "_value"])\n'
        '  |> sort(columns: ["_time"], desc: true)\n'
        f'  |> limit(n: {limit})'
    )

    with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
        tables = client.query_api().query(org=INFLUX_ORG, query=flux)

    werte = []
    for table in tables:
        for record in table.records:
            try:
                werte.append(float(record.get_value()))
            except (TypeError, ValueError):
                continue

    if len(werte) < 6:
        return {"anomalie": False, "grund": "zu wenige Datenpunkte in InfluxDB"}

    werte = list(reversed(werte[:fenster]))
    if len(werte) < 6:
        return {"anomalie": False, "grund": "zu wenige Datenpunkte nach Fensterung"}

    referenz = werte[:-1]
    aktuell_peak_db = werte[-1]
    mittel = statistics.mean(referenz)
    std = statistics.pstdev(referenz) or 0.01
    anomalie = abs(aktuell_peak_db - mittel) > 2.5 * std

    return {
        "anomalie": anomalie,
        "aktuell_peak_db": round(aktuell_peak_db, 2),
        "referenz_mittel": round(mittel, 2),
        "referenz_std": round(std, 2),
    }


def get_letzte_spectrum_messung() -> dict | None:
    """Liefert die neueste Messung aus audio_spectrum fuer die operative
    bezug_id (FK in audio_anomalien), einen konsistenten peak_db-Wert und
    peak_freq (fuer das Isolation-Forest-Modell, siehe
    shared/predictive_models.py)."""
    with _read_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, peak_freq, peak_db FROM audio_spectrum ORDER BY ts DESC LIMIT 1"
        )
        row = cur.fetchone()
    if not row:
        return None
    row["peak_db"] = round(float(row["peak_db"]), 2)
    row["peak_freq"] = round(float(row["peak_freq"]), 2)
    return row


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
