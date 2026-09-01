"""
LangGraph-Ablauf des Orchestrator-Agent: verarbeitet die Warteschlange
offener Akustik-Anomalien, delegiert je einen LAP-Ablauf an den
Wartungs-Agent und meldet das Ergebnis per A2A an den Report-Agent.
Ersetzt die vorherige for-Schleife in monitor.py - fachlich identisches
Verhalten, jetzt als Graph sichtbar (siehe /graph/mermaid und zum
Vergleich die didaktische Variante in langgraph-werkstatt/graph_aufgabe.py,
die denselben Ablauf vereinfacht fuer den Unterricht nachbildet).

Wichtig: die Sicherheitsentscheidung (Safety-Fence-Bestaetigung im
Wartungs-Agent, siehe lap_common/base.py) bleibt bewusst außerhalb dieses
Graphen und außerhalb jeder LLM-Einflussnahme - hier wird nur die
Reihenfolge der Arbeitsschritte modelliert, nicht die physische Freigabe
selbst. Der Orchestrator nutzt hier daher (anders als DB-/Report-Agent)
kein LLM.
"""
from typing import TypedDict
from uuid import uuid4

import httpx
from langgraph.graph import END, START, StateGraph

from shared import db_service

WARTUNGS_AGENT_URL = "http://localhost:9101"
REPORT_AGENT_URL = "http://localhost:9201"
REQUESTER_ID = "orchestrator-agent"


class OrchestratorStatus(TypedDict):
    offene: list[dict]
    aktuelle: dict | None
    ergebnis: dict | None
    berichte: list[str]


async def anomalien_lesen(status: OrchestratorStatus) -> dict:
    return {"offene": db_service.get_offene_anomalien()}


def gibt_es_offene(status: OrchestratorStatus) -> str:
    return "bearbeiten" if status["offene"] else "fertig"


def naechste_anomalie(status: OrchestratorStatus) -> dict:
    offene = list(status["offene"])
    aktuelle = offene.pop(0)
    return {"offene": offene, "aktuelle": aktuelle}


async def wartung_ausloesen(status: OrchestratorStatus) -> dict:
    aktuelle = status["aktuelle"]
    ergebnis = await _lap_aktion("schmierzyklus", {"anomalie_id": aktuelle["id"]})
    return {"ergebnis": ergebnis}


def anomalie_abschliessen(status: OrchestratorStatus) -> dict:
    db_service.markiere_anomalie_erledigt(status["aktuelle"]["id"])
    return {}


async def bericht_melden(status: OrchestratorStatus) -> dict:
    aktuelle = status["aktuelle"]
    text = (
        f"Vorausschauende Wartung ausgelöst (Anomalie #{aktuelle['id']}, "
        f"{aktuelle['peak_db']} dB vs. Referenz {aktuelle['referenz_mittel']} dB). "
        f"Ergebnis: {status['ergebnis']}"
    )
    await _melde_bericht_agent(text)
    return {"berichte": status["berichte"] + [text]}


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
                # Bewusst NICHT vom LLM entschieden, siehe Modul-Docstring.
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


def build_graph():
    workflow = StateGraph(OrchestratorStatus)
    workflow.add_node("anomalien_lesen", anomalien_lesen)
    workflow.add_node("naechste_anomalie", naechste_anomalie)
    workflow.add_node("wartung_ausloesen", wartung_ausloesen)
    workflow.add_node("anomalie_abschliessen", anomalie_abschliessen)
    workflow.add_node("bericht_melden", bericht_melden)

    workflow.add_edge(START, "anomalien_lesen")
    workflow.add_conditional_edges(
        "anomalien_lesen", gibt_es_offene, {"bearbeiten": "naechste_anomalie", "fertig": END}
    )
    workflow.add_edge("naechste_anomalie", "wartung_ausloesen")
    workflow.add_edge("wartung_ausloesen", "anomalie_abschliessen")
    workflow.add_edge("anomalie_abschliessen", "bericht_melden")
    workflow.add_conditional_edges(
        "bericht_melden", gibt_es_offene, {"bearbeiten": "naechste_anomalie", "fertig": END}
    )

    return workflow.compile()
