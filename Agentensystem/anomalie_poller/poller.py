"""
Uebergangsloesung fuer die von euch selbst im README als offen benannten
Punkte "Echtzeit-Inferenz auf dem Arduino" und "Alarm-System": bis es auf
dem Arduino UNO Q eine echte, trainierte Inferenz gibt, die aktiv eine
Anomalie-Nachricht verschickt, HOLT sich dieser Poller die neuesten
audio_spectrum-Eintraege und wendet dieselbe einfache Statistik-Heuristik
an wie das MCP-Tool 'pruefe_akustik_anomalie'.

Sobald ihr die echte Inferenz + ein MQTT-Topic dafuer habt, ersetzt ihr
NUR diese Datei durch einen MQTT-Listener (analog zu einem klassischen
mqtt_listener/akustik_listener.py) - shared/db_service.insert_anomalie()
und alles danach (audio_anomalien-Tabelle, Wartungs-Agent, Orchestrator)
bleiben unveraendert. Genau deshalb liegt die Erkennung hier bewusst
HINTER der db_service-Funktion und nicht direkt im Poller-Loop.

Start:  python -m anomalie_poller.poller
"""
import time

from shared import db_service

INTERVALL_SEKUNDEN = 15


def pruefzyklus() -> None:
    ergebnis = db_service.pruefe_akustik_anomalie(fenster=20)
    if not ergebnis.get("anomalie"):
        return

    bezug_id = ergebnis["bezug_id"]
    if db_service.anomalie_bereits_erfasst(bezug_id):
        return  # schon gemeldet, nicht doppelt eintragen

    db_service.insert_anomalie(
        bezug_id=bezug_id,
        peak_db=ergebnis["aktuell_peak_db"],
        mittel=ergebnis["referenz_mittel"],
        std=ergebnis["referenz_std"],
    )
    print(
        f"Anomalie erfasst: Messung #{bezug_id}, "
        f"{ergebnis['aktuell_peak_db']} dB vs. Referenz {ergebnis['referenz_mittel']} dB"
    )


if __name__ == "__main__":
    print(f"Anomalie-Poller gestartet (alle {INTERVALL_SEKUNDEN}s).")
    while True:
        try:
            pruefzyklus()
        except Exception as e:
            print(f"Fehler im Prüfzyklus: {e}")
        time.sleep(INTERVALL_SEKUNDEN)
