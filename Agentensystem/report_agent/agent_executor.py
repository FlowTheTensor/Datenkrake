"""
Report-Agent: nimmt vom Orchestrator gemeldete Ereignisse entgegen und
formuliert daraus eine Meldung über den in graph.py definierten
LangGraph-Ablauf (LLM-Versuch, sonst Template-Fallback).

Anders als beim Notenbeispiel ist der Report-Agent hier A2A-SERVER (der
Orchestrator ist für diese Interaktion der A2A-Client) - zeigt, dass
'Server' und 'Client' bei A2A Rollen pro Interaktion sind, keine feste
Eigenschaft eines Agenten.
"""
from typing_extensions import override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from report_agent.graph import build_graph

GRAPH = build_graph()


class BerichtAgentExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        ereignis_text = context.get_user_input() or "(keine Details übermittelt)"
        ergebnis = await GRAPH.ainvoke({"ereignis": ereignis_text, "meldung": ""})
        meldung = ergebnis["meldung"]
        print(meldung)  # in der Demo: Konsole statt E-Mail/Webshop-API
        event_queue.enqueue_event(new_agent_text_message(meldung))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("Abbrechen wird von diesem Agenten nicht unterstützt.")
