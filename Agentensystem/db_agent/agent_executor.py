"""
A2A-Fassade des DB-Agent - nutzt dieselbe shared/db_service.py wie der
Poller und der Orchestrator. Nach außen bietet dieser Agent den Skill
'telemetrie_abfragen' an.
"""
from typing_extensions import override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from shared import db_service


class TelemetrieAgentExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        text = (context.get_user_input() or "").lower()

        if "anomalie" in text or "wartung" in text:
            offene = db_service.get_offene_anomalien()
            antwort = (
                "\n".join(
                    f"#{a['id']}: {a['peak_db']} dB vs. Referenz {a['referenz_mittel']} dB "
                    f"(Messung #{a['bezug_id']})"
                    for a in offene
                )
                or "Keine offenen Anomalien."
            )
        elif "stats" in text or "statistik" in text:
            antwort = str(db_service.get_stats())
        else:
            antwort = "Ich kenne: 'anomalie'/'wartung' (offene Fälle), 'stats' (Statistik)."

        event_queue.enqueue_event(new_agent_text_message(antwort))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("Abbrechen wird von diesem Agenten nicht unterstützt.")
