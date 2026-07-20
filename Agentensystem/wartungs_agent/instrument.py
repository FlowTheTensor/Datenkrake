"""
Wartungs-Agent: LAP-Instrument-Agent fuer ein Diagnose-/Schmiergeraet.

Hinweis zum aktuellen Ausbaustand der Datenkrake: das Schema hat noch
KEIN Feld fuer "welche Station/welcher Motor" (aktuell genau ein
Arduino UNO Q mit einem Mikrofon). Bis ihr mehrere Arduino UNO Q an
verschiedenen Stationen betreibt (mit einer 'station'-Spalte in
audio_spectrum), bezieht sich jede Aktion hier auf "das ueberwachte
Objekt" allgemein statt auf eine konkrete Station. Sobald ihr das
erweitert, wandert 'station' einfach als zusaetzlicher Parameter durch
db_service, monitor.py und hierher durch.

Steuert AUSSCHLIESSLICH sein eigenes Zusatzgeraet, nie irgendeine
Produktionssteuerung.
"""
import random

from lap_common.base import Instrument, InstrumentCard, MeasurementResult
from shared import db_service

card = InstrumentCard(
    name="Wartungsgeraet-Akustik",
    description="Mobiles Diagnose- und Schmiergerät für den überwachten Motor/Förderabschnitt.",
    capabilities=["diagnosefahrt", "schmierzyklus"],
    physical_limits={"nur_im_leerlauf": True, "max_vibration_mm_s": 10.0},
)


class WartungsInstrument(Instrument):
    def __init__(self):
        super().__init__(card, hazardous_actions={"schmierzyklus"})

    def _execute(self, action: str, params: dict) -> MeasurementResult:
        anomalie_id = params.get("anomalie_id")

        if action == "diagnosefahrt":
            wert = round(random.uniform(1.0, 3.0), 2)
        elif action == "schmierzyklus":
            wert = round(random.uniform(0.8, 1.8), 2)
        else:
            raise ValueError(f"Unbekannte Aktion: {action}")

        ergebnis = MeasurementResult(
            value=wert, unit="mm/s", uncertainty=0.1, quantity="Vibration"
        )
        if anomalie_id is not None:
            db_service.log_wartungsereignis(anomalie_id, action, ergebnis.value)
        return ergebnis


instrument = WartungsInstrument()
