"""
A2A-Server-Teil des Orchestrator-Agent (für Statusabfragen von außen).
Der Orchestrator ist gleichzeitig A2A-Server (hier) und A2A-/LAP-Client
(siehe monitor.py) - die Rolle hängt von der jeweiligen Interaktion ab.
"""
from typing_extensions import override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from shared import db_service


class OrchestratorAgentExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        offene = db_service.get_offene_anomalien()
        antwort = f"{len(offene)} offene Anomalie(n) in Bearbeitung."
        event_queue.enqueue_event(new_agent_text_message(antwort))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("Abbrechen wird von diesem Agenten nicht unterstützt.")
