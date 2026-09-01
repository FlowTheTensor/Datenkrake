"""
Überwachungsschleife des Orchestrator-Agent - ruft in festem Intervall
den in graph.py definierten LangGraph-Ablauf auf (Anomalien lesen ->
LAP-Wartung auslösen -> abschließen -> Report-Agent benachrichtigen).
"""
import asyncio

from orchestrator_agent.graph import build_graph

GRAPH = build_graph()


async def pruefzyklus() -> None:
    ergebnis = await GRAPH.ainvoke(
        {"offene": [], "aktuelle": None, "ergebnis": None, "berichte": []}
    )
    for bericht in ergebnis["berichte"]:
        print(bericht)


async def loop(intervall_sekunden: int = 20) -> None:
    while True:
        try:
            await pruefzyklus()
        except Exception as e:
            print(f"Fehler im Prüfzyklus: {e}")
        await asyncio.sleep(intervall_sekunden)
