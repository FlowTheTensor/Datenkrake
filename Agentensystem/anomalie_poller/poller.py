"""
Uebergangsloesung fuer die von euch selbst im README als offen benannten
Punkte "Echtzeit-Inferenz auf dem Arduino" und "Alarm-System": bis es auf
dem Arduino UNO Q eine echte, trainierte Inferenz gibt, die aktiv eine
Anomalie-Nachricht verschickt, HOLT sich dieser Poller Messwerte aus dem
Operational Historian (InfluxDB) und wendet dieselbe einfache
Statistik-Heuristik an wie das MCP-Tool 'pruefe_akustik_anomalie'.

Sobald ihr die echte Inferenz + ein MQTT-Topic dafuer habt, ersetzt ihr
NUR diese Datei durch einen MQTT-Listener (analog zu einem klassischen
mqtt_listener/akustik_listener.py) - shared/db_service.insert_anomalie()
und alles danach (audio_anomalien-Tabelle, Wartungs-Agent, Orchestrator)
bleiben unveraendert. Genau deshalb liegt die Erkennung hier bewusst
HINTER der db_service-Funktion und nicht direkt im Poller-Loop.

Start:  python -m anomalie_poller.poller
"""
import os
import time

from shared import db_service, predictive_models

INTERVALL_SEKUNDEN = 15
QUELLE = os.environ.get("ANOMALIE_QUELLE", "influx").strip().lower()
METHODE = os.environ.get("ANOMALIE_METHODE", "zscore").strip().lower()


def _ergebnis_ermitteln() -> dict:
    """Liefert das Anomalie-Ergebnis - per Isolation Forest, wenn
    ANOMALIE_METHODE=isolation_forest gesetzt UND ein Modell trainiert
    wurde (siehe ml_training/), sonst per fester Mittelwert/Std-
    Heuristik. Ohne trainiertes Modell faellt die Methode automatisch auf
    die Heuristik zurueck, statt den Poller anzuhalten."""
    if METHODE == "isolation_forest":
        ergebnis = predictive_models.akustik_anomalie_ml()
        if ergebnis is not None:
            return ergebnis
        print(
            "Kein trainiertes Isolation-Forest-Modell gefunden (ml_training/models/), "
            "nutze zscore-Fallback. Erst 'python -m ml_training.train_isolation_forest_akustik' ausfuehren."
        )

    if QUELLE == "mariadb":
        return db_service.pruefe_akustik_anomalie(fenster=20)
    return db_service.pruefe_akustik_anomalie_influx(fenster=20)


def pruefzyklus() -> None:
    ergebnis = _ergebnis_ermitteln()

    if not ergebnis.get("anomalie"):
        return

    if "bezug_id" in ergebnis:
        bezug_id = ergebnis["bezug_id"]
        aktuell_peak_db = ergebnis["aktuell_peak_db"]
    else:
        letzte = db_service.get_letzte_spectrum_messung()
        if not letzte:
            print("Keine Messung in audio_spectrum vorhanden, ueberspringe.")
            return
        bezug_id = int(letzte["id"])
        aktuell_peak_db = letzte["peak_db"]

    if db_service.anomalie_bereits_erfasst(bezug_id):
        return  # schon gemeldet, nicht doppelt eintragen

    db_service.insert_anomalie(
        bezug_id=bezug_id,
        peak_db=aktuell_peak_db,
        mittel=ergebnis["referenz_mittel"],
        std=ergebnis["referenz_std"],
    )
    print(
        f"Anomalie erfasst: Messung #{bezug_id}, "
        f"{aktuell_peak_db} dB vs. Referenz {ergebnis['referenz_mittel']} dB"
    )


if __name__ == "__main__":
    print(
        f"Anomalie-Poller gestartet (alle {INTERVALL_SEKUNDEN}s, Quelle: {QUELLE}, Methode: {METHODE})."
    )
    while True:
        try:
            pruefzyklus()
        except Exception as e:
            print(f"Fehler im Prüfzyklus: {e}")
        time.sleep(INTERVALL_SEKUNDEN)
