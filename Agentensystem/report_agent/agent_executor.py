"""
Report-Agent: nimmt vom Orchestrator gemeldete Ereignisse entgegen und
formuliert daraus eine Meldung (z.B. für die Produktionsleitung oder,
wenn ein Auftrag betroffen ist, für den Webshop-Kunden).

Anders als beim Notenbeispiel ist der Report-Agent hier A2A-SERVER (der
Orchestrator ist für diese Interaktion der A2A-Client) - zeigt, dass
'Server' und 'Client' bei A2A Rollen pro Interaktion sind, keine feste
Eigenschaft eines Agenten.

Bewusst ohne LLM-Aufruf gehalten, damit die Demo ohne API-Key läuft. Der
naheliegende Ansatzpunkt für ein LLM wäre hier in _formuliere_meldung():
statt des festen Templates den rohen Ereignistext an Claude schicken und
eine adressatengerechte Formulierung erzeugen lassen.
"""
from datetime import datetime
from typing_extensions import override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message


class BerichtAgentExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        ereignis_text = context.get_user_input() or "(keine Details übermittelt)"
        meldung = _formuliere_meldung(ereignis_text)
        print(meldung)  # in der Demo: Konsole statt E-Mail/Webshop-API
        event_queue.enqueue_event(new_agent_text_message(meldung))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("Abbrechen wird von diesem Agenten nicht unterstützt.")


def _formuliere_meldung(ereignis_text: str) -> str:
    zeitstempel = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"[Produktionsbericht, {zeitstempel}]\n{ereignis_text}"
