"""
Startet den Wartungs-Agent als eigenständigen LAP-Server (Referenzimplementierung,
siehe lap_common/base.py).

Endpunkte:
  GET  /.well-known/instrument-card.json   -> InstrumentCard
  POST /reserve            {requester}
  POST /request-action     {requester, action, params}   -> ggf. Safety-Fence-Token
  POST /confirm-action      {requester, token}
  POST /release              {requester}

Start:  python -m wartungs_agent
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from lap_common.base import ReservationDenied, SafetyFenceRequired
from wartungs_agent.instrument import instrument

app = FastAPI(title="Wartungs-Agent (LAP)")


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
def request_action(req: ActionRequest):
    try:
        ergebnis = instrument.request_action(req.requester, req.action, req.params)
        return {"status": "abgeschlossen", "ergebnis": ergebnis.to_dict()}
    except SafetyFenceRequired as e:
        return {"status": "bestaetigung_erforderlich", "token": e.token}
    except ReservationDenied as e:
        raise HTTPException(status_code=409, detail=str(e))


class ConfirmRequest(BaseModel):
    requester: str
    token: str


@app.post("/confirm-action")
def confirm_action(req: ConfirmRequest):
    try:
        ergebnis = instrument.confirm_action(req.requester, req.token)
        return {"status": "abgeschlossen", "ergebnis": ergebnis.to_dict()}
    except (ReservationDenied, ValueError) as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/release")
def release(req: ReserveRequest):
    instrument.release(req.requester)
    return {"status": "freigegeben"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9101)
