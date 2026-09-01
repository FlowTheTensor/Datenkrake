"""
A2A-Server-Teil des Orchestrator-Agent (für Statusabfragen von außen).
Der Orchestrator ist gleichzeitig A2A-Server (hier) und A2A-/LAP-Client
(siehe monitor.py) - die Rolle hängt von der jeweiligen Interaktion ab.

Optional formuliert ein LLM die Statusmeldung natürlichsprachlich - fällt
bei Fehlern/Deaktivierung auf die feste Kurzform zurück. Die eigentliche
Überwachungs-/Wartungslogik (siehe graph.py, monitor.py) bleibt davon
unberührt und rein regelbasiert; das LLM trifft hier keine Entscheidung,
es formuliert nur den bereits feststehenden Zustand in Sprache.
"""
import os

from typing_extensions import override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from shared import db_service, llm_client

ORCHESTRATOR_USE_LLM_VAR = "ORCHESTRATOR_USE_LLM"
ORCHESTRATOR_LLM_URL = os.environ.get("ORCHESTRATOR_LLM_URL")
ORCHESTRATOR_LLM_MODEL = os.environ.get("ORCHESTRATOR_LLM_MODEL")
ORCHESTRATOR_LLM_API_KEY = os.environ.get("ORCHESTRATOR_LLM_API_KEY")
ORCHESTRATOR_LLM_TIMEOUT = os.environ.get("ORCHESTRATOR_LLM_TIMEOUT")

SYSTEM_PROMPT = (
    "Du formulierst kurze, sachliche Statusmeldungen für eine "
    "Produktionsleitstelle auf Deutsch. Nur Fakten aus der Eingabe, keine "
    "Vermutungen oder Handlungsempfehlungen."
)


class OrchestratorAgentExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        offene = db_service.get_offene_anomalien()
        antwort = await _status_formulieren(offene)
        event_queue.enqueue_event(new_agent_text_message(antwort))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("Abbrechen wird von diesem Agenten nicht unterstützt.")


async def _status_formulieren(offene: list[dict]) -> str:
    vorlage = f"{len(offene)} offene Anomalie(n) in Bearbeitung."
    if not llm_client.ist_aktiviert(ORCHESTRATOR_USE_LLM_VAR):
        return vorlage
    try:
        return await llm_client.chat_text(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Offene Anomalien: {offene}"},
            ],
            base_url=ORCHESTRATOR_LLM_URL,
            model=ORCHESTRATOR_LLM_MODEL,
            api_key=ORCHESTRATOR_LLM_API_KEY,
            timeout=int(ORCHESTRATOR_LLM_TIMEOUT) if ORCHESTRATOR_LLM_TIMEOUT else None,
        )
    except Exception as e:
        print(f"Orchestrator: LLM-Formulierung fehlgeschlagen, nutze Vorlage: {e}")
        return vorlage
