"""
LangGraph-Ablauf des DB-Agent: entscheidet zuerst, welches der beiden
Telemetrie-Werkzeuge die Anfrage beantwortet (per LLM-Tool-Calling, wenn
DB_AGENT_USE_LLM aktiv ist, sonst per Keyword-Abgleich), fuehrt es aus und
liefert die formatierte Antwort. Ersetzt die vorherige if/elif-Kette in
agent_executor.py - fachlich identisches Verhalten, jetzt als Graph
sichtbar (siehe /graph/mermaid und den Leitstand-Tab "Agenten-Graphen").
"""
import os
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from shared import db_service, llm_client

DB_AGENT_USE_LLM_VAR = "DB_AGENT_USE_LLM"
DB_AGENT_LLM_URL = os.environ.get("DB_AGENT_LLM_URL")
DB_AGENT_LLM_MODEL = os.environ.get("DB_AGENT_LLM_MODEL")
DB_AGENT_LLM_API_KEY = os.environ.get("DB_AGENT_LLM_API_KEY")
DB_AGENT_LLM_TIMEOUT = os.environ.get("DB_AGENT_LLM_TIMEOUT")

SYSTEM_PROMPT = (
    "Du bist der DB-Agent der Datenkrake. Waehle anhand der Nutzeranfrage "
    "genau eines der beiden angebotenen Werkzeuge aus."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "offene_anomalien",
            "description": "Liefert die aktuell offenen (noch nicht erledigten) Akustik-Anomalien.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "statistik",
            "description": "Liefert Anzahl und Durchschnitts-dB je Label ('gut'/'schlecht') aus der Audio-Telemetrie.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

Werkzeug = Literal["offene_anomalien", "statistik", "unbekannt"]


class DbAgentStatus(TypedDict):
    anfrage: str
    werkzeug: Werkzeug
    antwort: str


def _format_offene_anomalien() -> str:
    offene = db_service.get_offene_anomalien()
    return (
        "\n".join(
            f"#{a['id']}: {a['peak_db']} dB vs. Referenz {a['referenz_mittel']} dB "
            f"(Messung #{a['bezug_id']})"
            for a in offene
        )
        or "Keine offenen Anomalien."
    )


def _format_statistik() -> str:
    return str(db_service.get_stats())


def _werkzeug_per_keyword(text: str) -> Werkzeug:
    text = text.lower()
    if "anomalie" in text or "wartung" in text:
        return "offene_anomalien"
    if "stats" in text or "statistik" in text:
        return "statistik"
    return "unbekannt"


async def anfrage_verstehen(status: DbAgentStatus) -> dict:
    if llm_client.ist_aktiviert(DB_AGENT_USE_LLM_VAR):
        try:
            message = await llm_client.chat(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": status["anfrage"]},
                ],
                tools=TOOLS,
                base_url=DB_AGENT_LLM_URL,
                model=DB_AGENT_LLM_MODEL,
                api_key=DB_AGENT_LLM_API_KEY,
                timeout=int(DB_AGENT_LLM_TIMEOUT) if DB_AGENT_LLM_TIMEOUT else None,
            )
            calls = message.get("tool_calls") or []
            if calls:
                name = calls[0]["function"]["name"]
                if name in {"offene_anomalien", "statistik"}:
                    return {"werkzeug": name}
        except Exception as e:
            print(f"DB-Agent: LLM-Werkzeugwahl fehlgeschlagen, nutze Keyword-Fallback: {e}")

    return {"werkzeug": _werkzeug_per_keyword(status["anfrage"])}


def werkzeug_ausfuehren(status: DbAgentStatus) -> dict:
    if status["werkzeug"] == "offene_anomalien":
        return {"antwort": _format_offene_anomalien()}
    if status["werkzeug"] == "statistik":
        return {"antwort": _format_statistik()}
    return {"antwort": "Ich kenne: 'anomalie'/'wartung' (offene Fälle), 'stats' (Statistik)."}


def build_graph():
    workflow = StateGraph(DbAgentStatus)
    workflow.add_node("anfrage_verstehen", anfrage_verstehen)
    workflow.add_node("werkzeug_ausfuehren", werkzeug_ausfuehren)

    workflow.add_edge(START, "anfrage_verstehen")
    workflow.add_edge("anfrage_verstehen", "werkzeug_ausfuehren")
    workflow.add_edge("werkzeug_ausfuehren", END)

    return workflow.compile()
