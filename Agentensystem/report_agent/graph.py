"""
LangGraph-Ablauf des Report-Agent: versucht zuerst eine LLM-Formulierung
(wenn REPORT_USE_LLM aktiv ist), fällt bei Fehlern/Deaktivierung auf ein
festes Template zurück. Ersetzt die vorherige if/try-Kette in
agent_executor.py - fachlich identisches Verhalten, jetzt als Graph
sichtbar (siehe /graph/mermaid).
"""
import os
from datetime import datetime
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from shared import llm_client

REPORT_USE_LLM_VAR = "REPORT_USE_LLM"
REPORT_LLM_URL = os.environ.get("REPORT_LLM_URL")
REPORT_LLM_MODEL = os.environ.get("REPORT_LLM_MODEL")
REPORT_LLM_API_KEY = os.environ.get("REPORT_LLM_API_KEY")
REPORT_LLM_TIMEOUT = os.environ.get("REPORT_LLM_TIMEOUT")

SYSTEM_PROMPT = (
    "Du formulierst kurze, professionelle Produktionsmeldungen auf Deutsch. "
    "Liefere nur den finalen Meldungstext ohne Erklaerung."
)


class ReportStatus(TypedDict):
    ereignis: str
    meldung: str


async def llm_versuchen(status: ReportStatus) -> dict:
    if not llm_client.ist_aktiviert(REPORT_USE_LLM_VAR):
        return {"meldung": ""}
    try:
        text = await llm_client.chat_text(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Formuliere daraus eine kurze Produktionsmeldung. "
                        "Keine Halluzinationen, nur gegebene Fakten.\n\n"
                        f"Ereignis:\n{status['ereignis']}"
                    ),
                },
            ],
            base_url=REPORT_LLM_URL,
            model=REPORT_LLM_MODEL,
            api_key=REPORT_LLM_API_KEY,
            timeout=int(REPORT_LLM_TIMEOUT) if REPORT_LLM_TIMEOUT else None,
        )
        return {"meldung": text}
    except Exception as e:
        print(f"Report-Agent: LLM-Formulierung fehlgeschlagen, nutze Template-Fallback: {e}")
        return {"meldung": ""}


def hat_meldung(status: ReportStatus) -> str:
    return "fertig" if status["meldung"] else "template"


def template_formulieren(status: ReportStatus) -> dict:
    zeitstempel = datetime.now().strftime("%Y-%m-%d %H:%M")
    return {"meldung": f"[Produktionsbericht, {zeitstempel}]\n{status['ereignis']}"}


def build_graph():
    workflow = StateGraph(ReportStatus)
    workflow.add_node("llm_versuchen", llm_versuchen)
    workflow.add_node("template_formulieren", template_formulieren)

    workflow.add_edge(START, "llm_versuchen")
    workflow.add_conditional_edges(
        "llm_versuchen", hat_meldung, {"fertig": END, "template": "template_formulieren"}
    )
    workflow.add_edge("template_formulieren", END)

    return workflow.compile()
