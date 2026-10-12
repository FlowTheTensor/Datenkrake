# LangGraph-Werkstatt

Diese Werkstatt ist eine lokale, sichere Lernumgebung zum Modellieren von Agentenablaeufen. Schuelerinnen und Schueler bearbeiten Python-Code und sehen unmittelbar, wie daraus ein Mermaid-Diagramm und zwei simulierte Durchlaeufe entstehen.

Die Werkstatt kommuniziert nicht mit der Modellanlage, MariaDB, MCP, A2A oder LAP. Alle Agenten sind harmlose Python-Funktionen mit Beispielantworten. Sie eignet sich deshalb fuer jeden Schuelerlaptop und benoetigt keinen Zugang zum Datenkrake-Netz.

## Bezug und Start auf Windows

Es gibt zwei gleichwertige Verteilungswege. Fuer beide gilt: Den Ordner in einem beschreibbaren lokalen Bereich ablegen, zum Beispiel unter `Dokumente`.

### Variante A: ZIP-Datei

1. `langgraph-werkstatt.zip` herunterladen und entpacken.
2. Im entpackten Ordner `start.bat` doppelklicken.

### Variante B: Git Sparse Checkout (empfohlen)

Ein einzelner Unterordner kann nicht direkt geklont werden. Mit Sparse Checkout wird aber nur dieser Unterordner des Repositorys heruntergeladen:

```powershell
git clone --filter=blob:none --sparse https://github.com/FlowTheTensor/Datenkrake.git
cd Datenkrake
git sparse-checkout set Agentensystem/langgraph-werkstatt
cd Agentensystem/langgraph-werkstatt
.\start.bat
```

Bei einem privaten Repository muss die Lehrkraft den Schuelerinnen und Schuelern Leserechte geben oder eine andere Repository-URL bereitstellen.

### Arbeiten mit der Werkstatt

1. `start.bat` doppelklicken, falls es nicht bereits im Terminal gestartet wurde.
2. Beim ersten Start werden Python-Pakete aus dem Internet installiert. Danach oeffnet sich `http://127.0.0.1:8000` im Browser.
3. `graph_aufgabe.py` in VS Code bearbeiten, speichern und im Browser **Aktualisieren** waehlen.
4. Zum Beenden das schwarze Konsolenfenster schliessen oder `Strg+C` druecken.

Voraussetzung ist Python 3.10 oder neuer. Bei verwalteten Schuelergeraeten muss Python vorher durch die Schule installiert oder freigegeben sein.

## Was ist zu sehen?

| Bereich | Bedeutung |
| --- | --- |
| Graph-Definition | Der echte Python-Code aus `graph_aufgabe.py`. |
| Mermaid-Diagramm | Automatisch von LangGraph aus genau diesem Code erzeugter Ablaufgraph. |
| Hinweise | Warnungen zum Aufbau, z. B. ein Knoten ohne ausgehende Kante oder ein Knoten, der nie erreicht wird. |
| Simulation | Ein Durchlauf pro Eintrag in `SZENARIEN`: der **Weg** durch den Graphen (welche Knoten in welcher Reihenfolge), Hinweise bei Fehlern und der komplette **Endstatus**. |

`add_node(...)` erzeugt einen Knoten. `add_edge(...)` verbindet zwei Knoten. `add_conditional_edges(...)` erzeugt Verzweigungen. Die Funktion `entscheide_nach_freigabe()` waehlt anhand von `freigabe` einen Pfad.

Die Liste `SZENARIEN` am Anfang von `graph_aufgabe.py` legt fest, mit welchem Startstatus die Simulation laeuft. Felder, die ein Szenario nicht nennt, starten leer.

**Haeufige Stolperfalle:** Gibt ein Knoten ein Feld zurueck, das nicht in `AgentenStatus` eingetragen ist, verwirft LangGraph den Wert ohne Fehlermeldung. Im Endstatus fehlt das Feld dann einfach.

## Aufgabenstellung

**Ausgangslage:** Eine Anomalie wurde erkannt. Vor einer Diagnose muss ein Mensch entscheiden, ob das Diagnosegeraet genutzt werden darf. Anschliessend entsteht ein Report.

1. Lies `graph_aufgabe.py` und ordne jede `add_node`-Zeile einem Knoten im Diagramm zu.
2. Erklaere die beiden Pfeile nach dem Knoten `freigabe`. Welche Python-Zeilen legen sie fest?
3. Fuege zwischen `diagnose` und `report` einen Knoten `bewertung` ein. Schreibe eine Python-Funktion, die eine Bewertung in den Status eintraegt, verbinde den Knoten und aktualisiere die Anzeige. Pruefe im Endstatus, ob deine Bewertung ankommt.
4. Ergaenze einen weiteren Entscheidungspfad: Bei einer "kritischen" Anomalie (`schwere` = `"kritisch"`) soll eine zweite Freigabe erforderlich sein. Zeichne zuerst den erwarteten Ablauf auf Papier und setze ihn anschliessend mit `add_conditional_edges(...)` um. Ergaenze in `SZENARIEN` passende Durchlaeufe, z. B. "kritisch, beide Freigaben erteilt" und "kritisch, zweite Freigabe abgelehnt".
5. Vergleiche die Simulationen. Welche Knoten werden in allen Faellen erreicht, welche nur in einzelnen?

### Zusatzaufgabe: Der Graph fragt wirklich nach

Bisher steht die menschliche Entscheidung schon vorher im Szenario fest. Echte Agentensysteme halten an und warten auf einen Menschen ("Human in the loop"). In LangGraph geht das mit `interrupt()`:

```python
from langgraph.types import interrupt

def sicherheitsfreigabe(status: AgentenStatus) -> dict:
    antwort = interrupt("Darf das Diagnosegeraet genutzt werden?")
    return {"freigabe": antwort}
```

Die Simulation beantwortet die Frage mit den Werten aus der Liste `antworten` im Szenario, z. B. `{"name": "Freigabe", "status": {"schwere": "normal"}, "antworten": ["freigeben"]}`. Im Weg erscheint dann, wo der Graph angehalten hat und welche Antwort er bekommen hat.

- Warum braucht der Graph dafuer den Checkpointer (`compile(checkpointer=InMemorySaver())`)? Was passiert ohne ihn?
- Was zeigt die Simulation, wenn im Szenario keine Antwort hinterlegt ist?
- Warum sollte gerade die Sicherheitsfreigabe nie von einem Sprachmodell entschieden werden?

## Live-Modus mit AG-UI

Ueber den Link **Live-Modus mit AG-UI** oben auf der Seite (oder direkt `http://127.0.0.1:8000/live.html`) laeuft derselbe Graph aus `graph_aufgabe.py` Schritt fuer Schritt im Browser: Der gerade aktive Knoten leuchtet orange, erledigte Knoten werden gruen, ein wartender Knoten gelb. Rechts steht jede Meldung, die der Agent an den Browser schickt.

Diese Meldungen folgen dem offenen Protokoll **AG-UI** (Agent-User Interaction Protocol). Es legt fest, wie ein Agent einer Oberflaeche mitteilt, was er gerade tut, und wie die Oberflaeche antwortet. Damit ergaenzt es die Protokolle aus dem Agentensystem: MCP verbindet einen Agenten mit Werkzeugen, A2A Agenten untereinander, LAP einen Agenten mit einem Geraet - und AG-UI einen Agenten mit dem Menschen.

| AG-UI-Ereignis | Bedeutung in der Werkstatt |
| --- | --- |
| `RUN_STARTED` / `RUN_FINISHED` | Ein Durchlauf beginnt bzw. endet. `outcome` sagt wie: `success`, `interrupt` (Agent wartet auf eine Antwort) oder `cancelled`. |
| `STEP_STARTED` / `STEP_FINISHED` | Ein Knoten des Graphen beginnt bzw. ist fertig. |
| `STATE_SNAPSHOT` | Der komplette aktuelle Status (`AgentenStatus`). |
| `TEXT_MESSAGE_START` / `_CONTENT` / `_END` | Eine Textnachricht des Agenten, hier der Report. |
| `RUN_ERROR` | Fehler im Durchlauf, z. B. ein Tippfehler in einem Knoten. |

Interessant wird der Live-Modus mit der Zusatzaufgabe (`interrupt()`): Dann haelt der Graph an, im Browser erscheint die Frage, und **du** entscheidest. Die Antwort geht als neuer Durchlauf mit derselben `threadId` und dem Feld `resume` an den Agenten. Gibt der Knoten statt eines Textes ein Woerterbuch mit erlaubten Antworten an den Menschen weiter, erscheinen dafuer Knoepfe:

```python
antwort = interrupt({
    "message": "Darf das Diagnosegeraet genutzt werden?",
    "responseSchema": {"enum": ["freigeben", "ablehnen"]},
})
```

Die Szenarien liefern im Live-Modus nur den Startstatus, die Liste `antworten` wird nicht verwendet. Die Uebersetzung von LangGraph in AG-UI-Ereignisse steht kommentiert in `agui_bruecke.py`.

### Aufgaben zum Live-Modus

6. Starte ein Szenario und verfolge das Ereignisprotokoll. In welcher Reihenfolge kommen die Ereignisse? Welche Ereignisse gehoeren zu einem Knoten?
7. Setze die Zusatzaufgabe um und beantworte die Frage im Browser. Welches Ereignis beendet den ersten Durchlauf, und woran erkennt die Oberflaeche, dass sie fragen muss?
8. Nach deiner Antwort taucht `STEP_STARTED` fuer den Knoten `freigabe` ein zweites Mal auf. Warum fuehrt LangGraph den Knoten noch einmal aus? (Tipp: Was speichert der Checkpointer, was nicht?)
9. Vergleiche `threadId` und `runId` der beiden Durchlaeufe. Wozu braucht das Protokoll beide?

## Abgabe

Gib ausschliesslich die bearbeitete Datei `graph_aufgabe.py` ab. Sie enthaelt die Graph-Definition und ist klein genug, um gut verglichen und besprochen zu werden.

## Lehrkraft-Hinweis

Die Datei `langgraph-werkstatt.zip` ist als einfacher Offline-Verteilungsweg enthalten. Bei vorhandenem Git und Netzverbindung ist Sparse Checkout die bessere Wahl: Die Schueler erhalten den aktuellen Stand und koennen Aktualisierungen mit `git pull` laden. Vor der Verteilung einmal `start.bat` auf einem vergleichbaren Geraet testen. Wenn die Laptops keinen Internetzugang haben, muessen die Python-Pakete vorab in der virtuellen Umgebung installiert oder ein lokaler Paketspiegel bereitgestellt werden.

- **Internet im Browser:** Die Diagramm-Bibliothek Mermaid wird beim Oeffnen der Seite aus dem Internet geladen. Ohne Verbindung zeigt die Werkstatt statt des Diagramms den Mermaid-Quelltext an; Simulation und Hinweise funktionieren weiter.
- **Feste Versionen:** `requirements.txt` und der Mermaid-Link sind auf getestete Versionen festgelegt (LangGraph 1.2.14, AG-UI-Protokoll 1.0.0, Mermaid 11.6.0), damit ein spaeteres Update die Werkstatt nicht unbemerkt veraendert.
- **Kurzer Ablageort:** In sehr langen Ordnerpfaden (z. B. tief verschachtelt in OneDrive) bricht Python unter Windows beim Laden von LangGraph mit "DLL load failed ... Dateiname zu lang" ab. Die Werkstatt dann in einen kurzen Pfad wie `C:\lgw` oder direkt unter `Dokumente` legen.
- **Unterschied zum echten Orchestrator:** `orchestrator_agent/graph.py` arbeitet eine Warteschlange offener Anomalien in einer Schleife ab und haelt die Sicherheitsfreigabe bewusst ausserhalb des Graphen (sie liegt im Wartungs-Agent, siehe `lap_common/base.py`). Die Werkstatt zeigt die Freigabe dagegen als eigenen Knoten, damit Verzweigungen sichtbar werden. Dieser Unterschied eignet sich gut als Gespraechsanlass: Wo gehoert eine Sicherheitsentscheidung hin?
- **AG-UI ohne Fremdbibliothek im Browser:** Die Werkstatt nutzt nur das offizielle Python-Paket `ag-ui-protocol` fuer Ereignistypen und Kodierung. Die Uebersetzung aus LangGraph (`agui_bruecke.py`) und das Lesen des Ereignisstroms im Browser (`public/live.js`) sind bewusst selbst geschrieben, damit die Schueler das Protokoll sehen statt einer fertigen Bibliothek. Die offizielle Anbindung `ag-ui-langgraph` und Frontends wie CopilotKit nehmen diese Arbeit in echten Projekten ab.
- **Antwort-Knoepfe sind kein A2UI:** Die Knoepfe entstehen aus `responseSchema`, einem Feld von AG-UI. A2UI (Googles Standard, mit dem ein Agent ganze Oberflaechen als Daten beschreibt) ist bewusst nicht eingebaut, solange es vor Version 1.0 steht.