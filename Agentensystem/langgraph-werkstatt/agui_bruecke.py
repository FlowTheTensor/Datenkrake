"""Uebersetzt einen LangGraph-Durchlauf in AG-UI-Ereignisse (Live-Modus).

AG-UI (Agent-User Interaction Protocol) legt fest, wie ein Agent einer
Oberflaeche mitteilt, was er gerade tut. Der Browser schickt eine Anfrage
(RunAgentInput), der Agent antwortet mit einem Strom von Ereignissen
(Server-Sent Events, "data: {...}").

    LangGraph                         AG-UI-Ereignis
    --------------------------------  ----------------------------------------
    Durchlauf beginnt                 RUN_STARTED
    Knoten startet                    STEP_STARTED
    Knoten ist fertig                 STEP_FINISHED
    Status hat sich geaendert         STATE_SNAPSHOT
    Report liegt vor                  TEXT_MESSAGE_START / _CONTENT / _END
    interrupt() haelt den Graph an    RUN_FINISHED mit outcome "interrupt"
    Graph erreicht END                RUN_FINISHED mit outcome "success"
    Fehler                            RUN_ERROR

Die Antwort auf eine Unterbrechung kommt als neuer Lauf mit derselben
threadId und dem Feld "resume". Der Graph setzt dann dort fort, wo er
angehalten hat - moeglich ist das nur dank des Checkpointers (Gedaechtnis).
"""

import asyncio
from uuid import uuid4

from ag_ui.core import (
    Interrupt,
    RunAgentInput,
    RunErrorEvent,
    RunFinishedCancelledOutcome,
    RunFinishedEvent,
    RunFinishedInterruptOutcome,
    RunFinishedSuccessOutcome,
    RunStartedEvent,
    StateSnapshotEvent,
    StepFinishedEvent,
    StepStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
)
from ag_ui.encoder import EventEncoder
from langgraph.errors import GraphRecursionError
from langgraph.types import Command

SCHRITT_PAUSE = 0.6  # Sekunden pro Knoten, nur damit man im Browser zusehen kann
MAX_SCHRITTE = 50
MAX_OFFENE_DURCHLAEUFE = 50

# threadId -> kompilierter Graph. Ein angehaltener Durchlauf muss mit
# demselben Graph (und damit demselben Gedaechtnis) fortgesetzt werden.
_offene_graphen = {}


def als_agui_unterbrechung(unterbrechung) -> Interrupt:
    """interrupt("Frage?") oder interrupt({"message": ..., "responseSchema": ...})"""
    wert = unterbrechung.value
    ist_dict = isinstance(wert, dict)
    if isinstance(wert, str):
        nachricht = wert
    elif ist_dict:
        nachricht = wert.get("message")
    else:
        nachricht = str(wert)
    return Interrupt(
        id=unterbrechung.id,
        reason="langgraph:interrupt",
        message=nachricht,
        response_schema=wert.get("responseSchema") if ist_dict else None,
    )


def _merke_graph(thread_id: str, graph) -> None:
    _offene_graphen[thread_id] = graph
    while len(_offene_graphen) > MAX_OFFENE_DURCHLAEUFE:
        _offene_graphen.pop(next(iter(_offene_graphen)))


async def durchlauf(eingabe: RunAgentInput, lade_aufgabe):
    kodierer = EventEncoder()
    ids = {"thread_id": eingabe.thread_id, "run_id": eingabe.run_id}
    yield kodierer.encode(RunStartedEvent(**ids))

    try:
        if eingabe.resume:
            graph = _offene_graphen.get(eingabe.thread_id)
            if graph is None:
                raise ValueError("Dieser Durchlauf ist nicht mehr bekannt. Bitte neu starten.")
            antwort = eingabe.resume[0]
            if antwort.status == "cancelled":
                _offene_graphen.pop(eingabe.thread_id, None)
                yield kodierer.encode(
                    RunFinishedEvent(**ids, outcome=RunFinishedCancelledOutcome())
                )
                return
            start = Command(resume=antwort.payload)
        else:
            graph, _ = lade_aufgabe()
            if graph.checkpointer is None:
                raise ValueError(
                    "Der Live-Modus braucht ein Gedaechtnis: "
                    "workflow.compile(checkpointer=InMemorySaver())"
                )
            _merke_graph(eingabe.thread_id, graph)
            felder = list(graph.get_input_jsonschema()["properties"])
            start = {feld: "" for feld in felder} | (eingabe.state or {})

        config = {
            "configurable": {"thread_id": eingabe.thread_id},
            "recursion_limit": MAX_SCHRITTE,
        }
        status = {}
        async for modus, daten in graph.astream(start, config, stream_mode=["tasks", "values"]):
            if modus == "values":
                status = {k: v for k, v in daten.items() if k != "__interrupt__"}
                yield kodierer.encode(StateSnapshotEvent(snapshot=status))
            elif "result" in daten:
                yield kodierer.encode(StepFinishedEvent(step_name=daten["name"]))
            else:
                yield kodierer.encode(StepStartedEvent(step_name=daten["name"]))
                await asyncio.sleep(SCHRITT_PAUSE)

        offen = graph.get_state(config).interrupts
        if offen:
            unterbrechungen = [als_agui_unterbrechung(u) for u in offen]
            yield kodierer.encode(
                RunFinishedEvent(
                    **ids, outcome=RunFinishedInterruptOutcome(interrupts=unterbrechungen)
                )
            )
            return

        _offene_graphen.pop(eingabe.thread_id, None)
        if status.get("report"):
            nachricht_id = uuid4().hex
            yield kodierer.encode(TextMessageStartEvent(message_id=nachricht_id, role="assistant"))
            yield kodierer.encode(
                TextMessageContentEvent(message_id=nachricht_id, delta=str(status["report"]))
            )
            yield kodierer.encode(TextMessageEndEvent(message_id=nachricht_id))
        yield kodierer.encode(RunFinishedEvent(**ids, outcome=RunFinishedSuccessOutcome()))
    except GraphRecursionError:
        _offene_graphen.pop(eingabe.thread_id, None)
        yield kodierer.encode(
            RunErrorEvent(
                message=f"Nach {MAX_SCHRITTE} Schritten wurde END nicht erreicht - "
                "vermutlich eine Endlosschleife."
            )
        )
    except Exception as error:
        _offene_graphen.pop(eingabe.thread_id, None)
        yield kodierer.encode(RunErrorEvent(message=f"{type(error).__name__}: {error}"))
