"""
Trainiert ein Isolation-Forest-Modell auf den echten Akustik-Messungen
(audio_spectrum: peak_freq, peak_db) als Ersatz fuer die feste
Mittelwert/Standardabweichungs-Heuristik in shared/db_service.py.

Trainiert NUR auf mit 'gut' gelabelten Messungen (normaler Betrieb) - das
Modell lernt so die 'normale' Verteilung und markiert alles Abweichende
als Anomalie. Falls (noch) keine oder zu wenige Labels vorhanden sind,
faellt das Skript auf alle Messungen zurueck und meldet das deutlich.

Ausfuehren (aus Agentensystem/):
    pip install -r ml_training/requirements.txt
    python -m ml_training.train_isolation_forest_akustik
"""
import os

import joblib
import pymysql
from sklearn.ensemble import IsolationForest

MODELLE_ORDNER = os.path.join(os.path.dirname(__file__), "models")
MODELL_PFAD = os.path.join(MODELLE_ORDNER, "isolation_forest_akustik.joblib")

MIN_TRAININGSDATEN = 30


def lade_messungen() -> list[dict]:
    host = os.environ.get("DK_DB_HOST", "datenkrake.local")
    port = int(os.environ.get("DK_DB_PORT", "3306"))
    name = os.environ.get("DK_DB_NAME", "telemetry")
    user = os.environ.get("DK_READ_USER", "mcp_read")
    password = os.environ.get("DK_READ_PASSWORD", "changeMeMcp")

    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=name,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT label, peak_freq, peak_db FROM audio_spectrum ORDER BY ts")
            return cur.fetchall()
    finally:
        conn.close()


def main() -> None:
    os.makedirs(MODELLE_ORDNER, exist_ok=True)

    messungen = lade_messungen()
    print(f"{len(messungen)} Messungen aus audio_spectrum geladen.")

    gute = [m for m in messungen if m["label"] == "gut"]
    if len(gute) >= MIN_TRAININGSDATEN:
        trainingsdaten = gute
        print(f"Trainiere auf {len(gute)} mit 'gut' gelabelten Messungen.")
    else:
        trainingsdaten = messungen
        print(
            f"Nur {len(gute)} 'gut'-gelabelte Messungen (< {MIN_TRAININGSDATEN}) - "
            f"trainiere stattdessen auf allen {len(messungen)} Messungen."
        )

    if len(trainingsdaten) < MIN_TRAININGSDATEN:
        raise SystemExit(
            f"Zu wenige Messungen ({len(trainingsdaten)}) fuer ein sinnvolles Training - "
            "erst mehr Audiodaten sammeln (siehe ArduinoUnoQ/README.md)."
        )

    X = [[m["peak_freq"], m["peak_db"]] for m in trainingsdaten]

    modell = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
    modell.fit(X)

    joblib.dump(modell, MODELL_PFAD)
    print(f"Modell gespeichert unter {MODELL_PFAD}")

    schlechte = [m for m in messungen if m["label"] == "schlecht"]
    if schlechte:
        X_schlecht = [[m["peak_freq"], m["peak_db"]] for m in schlechte]
        vorhersagen = modell.predict(X_schlecht)
        erkannt = sum(1 for v in vorhersagen if v == -1)
        print(
            f"Validierung: {erkannt}/{len(schlechte)} als 'schlecht' gelabelte "
            "Messungen vom Modell als Anomalie erkannt."
        )


if __name__ == "__main__":
    main()
