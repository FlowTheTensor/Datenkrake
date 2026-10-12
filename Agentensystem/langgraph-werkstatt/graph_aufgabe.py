"""Bearbeite diese Datei: Aus dem Code entsteht das Mermaid-Diagramm."""

from typing import Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class AgentenStatus(TypedDict):
    # Jedes Feld, das ein Knoten zurueckgibt, muss hier eingetragen sein.
    # Felder, die hier fehlen, verwirft LangGraph OHNE Fehlermeldung.
    anomalie: str
    schwere: Literal["normal", "kritisch"]
    freigabe: Literal["freigeben", "ablehnen"]
    diagnose: str
    report: str


# Jedes Szenario ist ein Durchlauf mit eigenem Startstatus. Nicht genannte
# Felder starten leer. Fuer Aufgabe 4 hier weitere Szenarien ergaenzen.
SZENARIEN = [
    {"name": "Freigabe", "status": {"schwere": "normal", "freigabe": "freigeben"}},
    {"name": "Ablehnung", "status": {"schwere": "normal", "freigabe": "ablehnen"}},
]


def anomaliestatus_lesen(status: AgentenStatus) -> dict:
    return {"anomalie": "Ungewoehnliche Schwingung erkannt"}


def sicherheitsfreigabe(status: AgentenStatus) -> dict:
    # Vereinfachung: Die menschliche Entscheidung steht schon im Szenario.
    # Wie der Graph wirklich anhalten und fragen kann, zeigt die Zusatzaufgabe.
    return {}


def entscheide_nach_freigabe(status: AgentenStatus) -> str:
    return status["freigabe"]


def diagnose_ausfuehren(status: AgentenStatus) -> dict:
    return {"diagnose": "Messung durch Wartungs-Agent ausgefuehrt"}


def ablehnung_protokollieren(status: AgentenStatus) -> dict:
    return {"diagnose": "Diagnose nach menschlicher Ablehnung nicht gestartet"}


def report_erstellen(status: AgentenStatus) -> dict:
    return {"report": f"Report: {status['diagnose']}"}


def build_graph():
    workflow = StateGraph(AgentenStatus)

    # Aufgabe 3 und 4: Neue Knoten hier mit add_node ergaenzen ...
    workflow.add_node("anomaliestatus", anomaliestatus_lesen)
    workflow.add_node("freigabe", sicherheitsfreigabe)
    workflow.add_node("diagnose", diagnose_ausfuehren)
    workflow.add_node("ablehnung", ablehnung_protokollieren)
    workflow.add_node("report", report_erstellen)

    # ... und hier mit add_edge bzw. add_conditional_edges verbinden.
    workflow.add_edge(START, "anomaliestatus")
    workflow.add_edge("anomaliestatus", "freigabe")
    workflow.add_conditional_edges(
        "freigabe",
        entscheide_nach_freigabe,
        {"freigeben": "diagnose", "ablehnen": "ablehnung"},
    )
    workflow.add_edge("diagnose", "report")
    workflow.add_edge("ablehnung", "report")
    workflow.add_edge("report", END)

    # Der Checkpointer ist das Gedaechtnis des Graphen. Er merkt sich den
    # Status nach jedem Schritt, damit ein Durchlauf anhalten und spaeter
    # fortgesetzt werden kann (siehe Zusatzaufgabe).
    return workflow.compile(checkpointer=InMemorySaver())
