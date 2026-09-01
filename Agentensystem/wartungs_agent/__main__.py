"""
Startet den Wartungs-Agent als eigenständigen LAP-Server (Referenzimplementierung,
siehe lap_common/base.py).

Endpunkte:
  GET  /.well-known/instrument-card.json   -> InstrumentCard
  POST /reserve            {requester}
  POST /request-action     {requester, action, params}   -> ggf. Safety-Fence-Token
  POST /confirm-action      {requester, token}
  POST /release              {requester}

Optional kommentiert ein LLM das Messergebnis kurz in Sprache (siehe
_kommentar unten). Das ist rein deskriptiv und läuft NACH der Aktion -
die Safety-Fence-Entscheidung selbst (ob eine Bestätigung nötig ist)
bleibt vollständig in lap_common/base.py/instrument.py geregelt und wird
vom LLM weder gesehen noch beeinflusst.

Start:  python -m wartungs_agent
"""
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from lap_common.base import ReservationDenied, SafetyFenceRequired
from shared import llm_client
from wartungs_agent.instrument import instrument

WARTUNGS_AGENT_USE_LLM_VAR = "WARTUNGS_AGENT_USE_LLM"
WARTUNGS_AGENT_LLM_URL = os.environ.get("WARTUNGS_AGENT_LLM_URL")
WARTUNGS_AGENT_LLM_MODEL = os.environ.get("WARTUNGS_AGENT_LLM_MODEL")
WARTUNGS_AGENT_LLM_API_KEY = os.environ.get("WARTUNGS_AGENT_LLM_API_KEY")
WARTUNGS_AGENT_LLM_TIMEOUT = os.environ.get("WARTUNGS_AGENT_LLM_TIMEOUT")

SYSTEM_PROMPT = (
    "Du kommentierst eine Vibrationsmessung eines Wartungsgeräts kurz und "
    "sachlich auf Deutsch (ein Satz). Nur Einordnung des Messwerts, keine "
    "Handlungsempfehlung."
)

app = FastAPI(title="Wartungs-Agent (LAP)")


async def _kommentar(ergebnis: dict) -> str | None:
    """Rein sprachliche Einordnung des Messergebnisses per LLM - fließt
    NICHT in die Safety-Fence-Entscheidung ein (siehe Moduldocstring)."""
    if not llm_client.ist_aktiviert(WARTUNGS_AGENT_USE_LLM_VAR):
        return None
    grenze = instrument.card.physical_limits.get("max_vibration_mm_s")
    try:
        return await llm_client.chat_text(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Messwert: {ergebnis['value']} {ergebnis['unit']} "
                        f"({ergebnis['quantity']}). Grenzwert: {grenze} mm/s."
                    ),
                },
            ],
            base_url=WARTUNGS_AGENT_LLM_URL,
            model=WARTUNGS_AGENT_LLM_MODEL,
            api_key=WARTUNGS_AGENT_LLM_API_KEY,
            timeout=int(WARTUNGS_AGENT_LLM_TIMEOUT) if WARTUNGS_AGENT_LLM_TIMEOUT else None,
        )
    except Exception as e:
        print(f"Wartungs-Agent: LLM-Kommentar fehlgeschlagen: {e}")
        return None


@app.get("/.well-known/instrument-card.json")
def get_card():
    return instrument.card.to_dict()


class ReserveRequest(BaseModel):
    requester: str


@app.post("/reserve")
def reserve(req: ReserveRequest):
    try:
        instrument.reserve(req.requester)
        return {"status": "reserviert"}
    except ReservationDenied as e:
        raise HTTPException(status_code=409, detail=str(e))


class ActionRequest(BaseModel):
    requester: str
    action: str
    params: dict


@app.post("/request-action")
async def request_action(req: ActionRequest):
    try:
        ergebnis = instrument.request_action(req.requester, req.action, req.params)
        ergebnis_dict = ergebnis.to_dict()
        kommentar = await _kommentar(ergebnis_dict)
        if kommentar:
            ergebnis_dict["kommentar"] = kommentar
        return {"status": "abgeschlossen", "ergebnis": ergebnis_dict}
    except SafetyFenceRequired as e:
        return {"status": "bestaetigung_erforderlich", "token": e.token}
    except ReservationDenied as e:
        raise HTTPException(status_code=409, detail=str(e))


class ConfirmRequest(BaseModel):
    requester: str
    token: str


@app.post("/confirm-action")
async def confirm_action(req: ConfirmRequest):
    try:
        ergebnis = instrument.confirm_action(req.requester, req.token)
        ergebnis_dict = ergebnis.to_dict()
        kommentar = await _kommentar(ergebnis_dict)
        if kommentar:
            ergebnis_dict["kommentar"] = kommentar
        return {"status": "abgeschlossen", "ergebnis": ergebnis_dict}
    except (ReservationDenied, ValueError) as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/release")
def release(req: ReserveRequest):
    instrument.release(req.requester)
    return {"status": "freigegeben"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9101)
