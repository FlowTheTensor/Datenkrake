"""Erzeugt die Darstellung und stellt die Werkstatt unter localhost bereit."""

import sys
from importlib import import_module
from pathlib import Path
from uuid import uuid4

from ag_ui.core import RunAgentInput
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from langgraph.errors import GraphRecursionError
from langgraph.types import Command

import agui_bruecke

ROOT = Path(__file__).parent
PUBLIC = ROOT / "public"
MAX_SCHRITTE = 50

# Kein __pycache__: schnelle Aenderungen an graph_aufgabe.py innerhalb
# derselben Sekunde koennten sonst eine veraltete Fassung laden.
sys.dont_write_bytecode = True

app = FastAPI(title="LangGraph-Werkstatt")


def lade_aufgabe():
    # Frisch importieren statt reload(): reload() behaelt Namen, die im Code
    # inzwischen geloescht wurden (z. B. eine entfernte SZENARIEN-Liste).
    sys.modules.pop("graph_aufgabe", None)
    modul = import_module("graph_aufgabe")
    szenarien = getattr(modul, "SZENARIEN", None)
    if not szenarien:
        raise ValueError("In graph_aufgabe.py fehlt die Liste SZENARIEN.")
    return modul.build_graph(), szenarien


def strukturhinweise(graph) -> list[str]:
    """Findet Knoten, die LangGraph ohne Fehlermeldung akzeptiert, die aber
    den Ablauf ins Leere laufen lassen."""
    zeichnung = graph.get_graph()
    mit_eingang = {kante.target for kante in zeichnung.edges}
    # Ausgaenge aus dem Builder statt aus der Zeichnung: get_graph() ergaenzt
    # fuer Knoten ohne Ausgang eine unsichtbare Kante nach END.
    builder = graph.builder
    mit_ausgang = {quelle for quelle, _ in builder.edges} | set(builder.branches)
    mit_ausgang |= {quelle for quellen, _ in builder.waiting_edges for quelle in quellen}
    hinweise = []
    for knoten in zeichnung.nodes:
        if knoten in ("__start__", "__end__"):
            continue
        if knoten not in mit_eingang:
            hinweise.append(f"Knoten '{knoten}' hat keine eingehende Kante und wird nie erreicht.")
        if knoten not in mit_ausgang:
            hinweise.append(
                f"Knoten '{knoten}' hat keine ausgehende Kante. Ein Durchlauf endet dort, "
                "ohne END zu erreichen."
            )
    return hinweise


def durchlauf(graph, felder: list[str], szenario: dict) -> dict:
    name = szenario.get("name", "Ohne Namen")
    vorgabe = szenario.get("status", {})
    hinweise = [
        f"Das Szenario setzt '{feld}', das Feld fehlt aber in AgentenStatus und wird verworfen."
        for feld in vorgabe
        if feld not in felder
    ]
    status = {feld: "" for feld in felder} | vorgabe
    antworten = list(szenario.get("antworten", []))
    config = {"configurable": {"thread_id": uuid4().hex}, "recursion_limit": MAX_SCHRITTE}
    weg = []
    eingabe = status

    try:
        while True:
            frage = None
            for modus, daten in graph.stream(eingabe, config, stream_mode=["updates", "values"]):
                if modus == "values":
                    status = {k: v for k, v in daten.items() if k != "__interrupt__"}
                    continue
                for knoten in daten:
                    if knoten == "__interrupt__":
                        frage = daten[knoten][0].value
                    else:
                        weg.append({"knoten": knoten})

            if frage is None:
                break
            if graph.checkpointer is None:
                hinweise.append(
                    "interrupt() braucht ein Gedaechtnis: "
                    "workflow.compile(checkpointer=InMemorySaver())"
                )
                break
            if not antworten:
                weg.append({"frage": str(frage), "antwort": None})
                hinweise.append(
                    "Der Graph wartet auf eine Antwort. Ergaenze im Szenario eine Liste "
                    "'antworten', z. B. \"antworten\": [\"freigeben\"]."
                )
                break
            antwort = antworten.pop(0)
            weg.append({"frage": str(frage), "antwort": antwort})
            eingabe = Command(resume=antwort)
    except GraphRecursionError:
        hinweise.append(
            f"Nach {MAX_SCHRITTE} Schritten wurde END nicht erreicht - vermutlich eine Endlosschleife."
        )
    except Exception as error:
        hinweise.append(f"Fehler waehrend des Durchlaufs: {type(error).__name__}: {error}")

    return {"name": name, "weg": weg, "status": status, "hinweise": hinweise}


@app.get("/api/quellcode")
def quellcode():
    return {"code": (ROOT / "graph_aufgabe.py").read_text(encoding="utf-8")}


@app.get("/api/werkstatt")
def werkstatt_daten():
    try:
        graph, szenarien = lade_aufgabe()
        mermaid = graph.get_graph().draw_mermaid()
        (PUBLIC / "graph.mmd").write_text(mermaid, encoding="utf-8")

        felder = list(graph.get_input_jsonschema()["properties"])
        return {
            "mermaid": mermaid,
            "hinweise": strukturhinweise(graph),
            "szenarien": [durchlauf(graph, felder, szenario) for szenario in szenarien],
        }
    except Exception as error:
        return JSONResponse(status_code=400, content={"fehler": str(error)})


@app.get("/api/live")
def live_vorbereitung():
    """Diagramm und Szenarien fuer den Live-Modus, ohne Simulation."""
    try:
        graph, szenarien = lade_aufgabe()
        return {
            "mermaid": graph.get_graph().draw_mermaid(),
            "hinweise": strukturhinweise(graph),
            "szenarien": [
                {"name": s.get("name", "Ohne Namen"), "status": s.get("status", {})}
                for s in szenarien
            ],
        }
    except Exception as error:
        return JSONResponse(status_code=400, content={"fehler": str(error)})


@app.post("/api/agui")
async def agui(eingabe: RunAgentInput):
    """AG-UI-Endpunkt: nimmt RunAgentInput entgegen, antwortet mit einem Ereignisstrom."""
    return StreamingResponse(
        agui_bruecke.durchlauf(eingabe, lade_aufgabe), media_type="text/event-stream"
    )


app.mount("/", StaticFiles(directory=PUBLIC, html=True), name="public")
