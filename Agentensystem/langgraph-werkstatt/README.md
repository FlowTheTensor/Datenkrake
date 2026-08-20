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
| Simulation | Ergebnis fuer die zwei moeglichen menschlichen Entscheidungen: Freigabe oder Ablehnung. |

`add_node(...)` erzeugt einen Knoten. `add_edge(...)` verbindet zwei Knoten. `add_conditional_edges(...)` erzeugt Verzweigungen. Die Funktion `entscheide_nach_freigabe()` waehlt anhand von `freigabe` einen Pfad.

## Aufgabenstellung

**Ausgangslage:** Eine Anomalie wurde erkannt. Vor einer Diagnose muss ein Mensch entscheiden, ob das Diagnosegeraet genutzt werden darf. Anschliessend entsteht ein Report.

1. Lies `graph_aufgabe.py` und ordne jede `add_node`-Zeile einem Knoten im Diagramm zu.
2. Erklaere die beiden Pfeile nach dem Knoten `freigabe`. Welche Python-Zeilen legen sie fest?
3. Fuege zwischen `diagnose` und `report` einen Knoten `bewertung` ein. Schreibe eine Python-Funktion, die eine Bewertung in den Status eintraegt, verbinde den Knoten und aktualisiere die Anzeige.
4. Ergaenze einen weiteren Entscheidungspfad: Bei einer "kritischen" Anomalie soll eine zweite Freigabe erforderlich sein. Zeichne zuerst den erwarteten Ablauf auf Papier und setze ihn anschliessend mit `add_conditional_edges(...)` um.
5. Vergleiche die Simulationen fuer Freigabe und Ablehnung. Welche Knoten werden in beiden Faellen erreicht, welche nur in einem?

## Abgabe

Gib ausschliesslich die bearbeitete Datei `graph_aufgabe.py` ab. Sie enthaelt die Graph-Definition und ist klein genug, um gut verglichen und besprochen zu werden.

## Lehrkraft-Hinweis

Die Datei `langgraph-werkstatt.zip` ist als einfacher Offline-Verteilungsweg enthalten. Bei vorhandenem Git und Netzverbindung ist Sparse Checkout die bessere Wahl: Die Schueler erhalten den aktuellen Stand und koennen Aktualisierungen mit `git pull` laden. Vor der Verteilung einmal `start.bat` auf einem vergleichbaren Geraet testen. Wenn die Laptops keinen Internetzugang haben, muessen die Python-Pakete vorab in der virtuellen Umgebung installiert oder ein lokaler Paketspiegel bereitgestellt werden.