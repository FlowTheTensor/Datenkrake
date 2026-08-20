"""Bearbeite diese Datei: Aus dem Code entsteht das Mermaid-Diagramm."""

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class AgentenStatus(TypedDict):
    anomalie: str
    freigabe: Literal["freigeben", "ablehnen"]
    diagnose: str
    report: str


def anomaliestatus_lesen(status: AgentenStatus) -> dict:
    return {"anomalie": "Ungewoehnliche Schwingung erkannt"}


def sicherheitsfreigabe(status: AgentenStatus) -> dict:
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

    # Aufgabe 1: Ergaenze einen eigenen Knoten und verbinde ihn mit dem Ablauf.
    workflow.add_node("anomaliestatus", anomaliestatus_lesen)
    workflow.add_node("freigabe", sicherheitsfreigabe)
    workflow.add_node("diagnose", diagnose_ausfuehren)
    workflow.add_node("ablehnung", ablehnung_protokollieren)
    workflow.add_node("report", report_erstellen)

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

    return workflow.compile()