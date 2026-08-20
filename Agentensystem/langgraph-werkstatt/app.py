"""Erzeugt die Darstellung und stellt die Werkstatt unter localhost bereit."""

from importlib import import_module, reload
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent
PUBLIC = ROOT / "public"

app = FastAPI(title="LangGraph-Werkstatt")


def lade_graph():
    modul = import_module("graph_aufgabe")
    return reload(modul).build_graph()


@app.get("/api/quellcode")
def quellcode():
    return {"code": (ROOT / "graph_aufgabe.py").read_text(encoding="utf-8")}


@app.get("/api/werkstatt")
def werkstatt_daten():
    try:
        graph = lade_graph()
        mermaid = graph.get_graph().draw_mermaid()
        (PUBLIC / "graph.mmd").write_text(mermaid, encoding="utf-8")

        basis_status = {
            "anomalie": "",
            "diagnose": "",
            "report": "",
        }
        freigabe = graph.invoke({**basis_status, "freigabe": "freigeben"})
        ablehnung = graph.invoke({**basis_status, "freigabe": "ablehnen"})
        return {"mermaid": mermaid, "freigabe": freigabe, "ablehnung": ablehnung}
    except Exception as error:
        return JSONResponse(status_code=400, content={"fehler": str(error)})


app.mount("/", StaticFiles(directory=PUBLIC, html=True), name="public")