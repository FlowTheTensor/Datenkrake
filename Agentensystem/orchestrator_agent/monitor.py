"""
Überwachungsschleife des Orchestrator-Agent.

Liest offene Einträge aus audio_anomalien (vom anomalie_poller befüllt)
und delegiert je einen vollständigen LAP-Ablauf an den Wartungs-Agent.
Meldet danach an den Report-Agent (A2A) und markiert die Anomalie als
erledigt.
"""
import asyncio
from uuid import uuid4

import httpx

from shared import db_service

WARTUNGS_AGENT_URL = "http://localhost:9101"
REPORT_AGENT_URL = "http://localhost:9201"
REQUESTER_ID = "orchestrator-agent"


async def _lap_aktion(action: str, params: dict) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(f"{WARTUNGS_AGENT_URL}/reserve", json={"requester": REQUESTER_ID})
        try:
            resp = await client.post(
                f"{WARTUNGS_AGENT_URL}/request-action",
                json={"requester": REQUESTER_ID, "action": action, "params": params},
            )
            data = resp.json()
            if data.get("status") == "bestaetigung_erforderlich":
                # Demo: automatisch bestätigt. In echt: Aufsichtsperson fragen.
                confirm = await client.post(
                    f"{WARTUNGS_AGENT_URL}/confirm-action",
                    json={"requester": REQUESTER_ID, "token": data["token"]},
                )
                data = confirm.json()
            return data
        finally:
            await client.post(f"{WARTUNGS_AGENT_URL}/release", json={"requester": REQUESTER_ID})


async def _melde_bericht_agent(text: str) -> None:
    try:
        from a2a.client import A2ACardResolver, A2AClient
        from a2a.types import MessageSendParams, SendMessageRequest

        async with httpx.AsyncClient(timeout=10) as httpx_client:
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=REPORT_AGENT_URL)
            card = await resolver.get_agent_card()
            client = A2AClient(httpx_client=httpx_client, agent_card=card)
            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(
                    message={
                        "role": "user",
                        "parts": [{"type": "text", "text": text}],
                        "messageId": str(uuid4()),
                    }
                ),
            )
            await client.send_message(request)
    except Exception as e:
        print(f"Konnte Report-Agent nicht erreichen: {e}")


async def pruefzyklus() -> None:
    for anomalie in db_service.get_offene_anomalien():
        print(f"Anomalie #{anomalie['id']} (Messung #{anomalie['bezug_id']}) -> Wartung")
        ergebnis = await _lap_aktion("schmierzyklus", {"anomalie_id": anomalie["id"]})
        db_service.markiere_anomalie_erledigt(anomalie["id"])
        await _melde_bericht_agent(
            f"Vorausschauende Wartung ausgelöst (Anomalie #{anomalie['id']}, "
            f"{anomalie['peak_db']} dB vs. Referenz {anomalie['referenz_mittel']} dB). "
            f"Ergebnis: {ergebnis}"
        )


async def loop(intervall_sekunden: int = 20) -> None:
    while True:
        try:
            await pruefzyklus()
        except Exception as e:
            print(f"Fehler im Prüfzyklus: {e}")
        await asyncio.sleep(intervall_sekunden)
