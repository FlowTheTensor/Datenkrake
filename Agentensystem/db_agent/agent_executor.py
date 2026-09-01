"""
A2A-Fassade des DB-Agent - ruft den in graph.py definierten LangGraph-
Ablauf auf (LLM-Werkzeugwahl bzw. Keyword-Fallback, siehe dort). Nach
außen bietet dieser Agent weiterhin den Skill 'telemetrie_abfragen' an.
"""
from typing_extensions import override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from db_agent.graph import build_graph

GRAPH = build_graph()


class TelemetrieAgentExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        ergebnis = await GRAPH.ainvoke(
            {"anfrage": context.get_user_input() or "", "werkzeug": "unbekannt", "antwort": ""}
        )
        event_queue.enqueue_event(new_agent_text_message(ergebnis["antwort"]))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("Abbrechen wird von diesem Agenten nicht unterstützt.")
