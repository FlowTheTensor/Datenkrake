"""
Report-Agent: nimmt vom Orchestrator gemeldete Ereignisse entgegen und
formuliert daraus eine Meldung (z.B. für die Produktionsleitung oder,
wenn ein Auftrag betroffen ist, für den Webshop-Kunden).

Anders als beim Notenbeispiel ist der Report-Agent hier A2A-SERVER (der
Orchestrator ist für diese Interaktion der A2A-Client) - zeigt, dass
'Server' und 'Client' bei A2A Rollen pro Interaktion sind, keine feste
Eigenschaft eines Agenten.

Optional kann ein LLM fuer die Formulierung genutzt werden.
Wenn der LLM-Aufruf fehlschlaegt oder deaktiviert ist, faellt der Agent
automatisch auf das feste Template zurueck.
"""
import os
from datetime import datetime

import httpx
from typing_extensions import override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

REPORT_USE_LLM = os.environ.get("REPORT_USE_LLM", "false").strip().lower()
REPORT_LLM_URL = os.environ.get("REPORT_LLM_URL", "http://localhost:1234")
REPORT_LLM_MODEL = os.environ.get("REPORT_LLM_MODEL", "local-model")
REPORT_LLM_API_KEY = os.environ.get("REPORT_LLM_API_KEY")
REPORT_LLM_TIMEOUT = int(os.environ.get("REPORT_LLM_TIMEOUT", "30"))

SYSTEM_PROMPT = (
    "Du formulierst kurze, professionelle Produktionsmeldungen auf Deutsch. "
    "Liefere nur den finalen Meldungstext ohne Erklaerung."
)


class BerichtAgentExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        ereignis_text = context.get_user_input() or "(keine Details übermittelt)"
        meldung = await _formuliere_meldung(ereignis_text)
        print(meldung)  # in der Demo: Konsole statt E-Mail/Webshop-API
        event_queue.enqueue_event(new_agent_text_message(meldung))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("Abbrechen wird von diesem Agenten nicht unterstützt.")


def _llm_aktiviert() -> bool:
    return REPORT_USE_LLM in {"1", "true", "yes", "on"}


async def _formuliere_meldung(ereignis_text: str) -> str:
    if _llm_aktiviert():
        try:
            llm_meldung = await _formuliere_mit_llm(ereignis_text)
            if llm_meldung:
                return llm_meldung
        except Exception as e:
            print(f"LLM-Formulierung fehlgeschlagen, nutze Template-Fallback: {e}")

    return _formuliere_template(ereignis_text)


async def _formuliere_mit_llm(ereignis_text: str) -> str:
    headers = {"Content-Type": "application/json"}
    if REPORT_LLM_API_KEY:
        headers["Authorization"] = f"Bearer {REPORT_LLM_API_KEY}"

    payload = {
        "model": REPORT_LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Formuliere daraus eine kurze Produktionsmeldung. "
                    "Keine Halluzinationen, nur gegebene Fakten.\n\n"
                    f"Ereignis:\n{ereignis_text}"
                ),
            },
        ],
        "temperature": 0.2,
    }

    async with httpx.AsyncClient(timeout=REPORT_LLM_TIMEOUT) as client:
        response = await client.post(
            f"{REPORT_LLM_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    text = (text or "").strip()
    if not text:
        raise ValueError("LLM lieferte keinen Meldungstext")
    return text


def _formuliere_template(ereignis_text: str) -> str:
    zeitstempel = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"[Produktionsbericht, {zeitstempel}]\n{ereignis_text}"
