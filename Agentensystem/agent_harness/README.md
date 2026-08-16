<img align="right" src="../../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# Agent Harness

## Was ist ein "Harness"?

Ein **Harness** ist der Code, der aus einem rohen Sprachmodell (das nur
Text gegen Text tauscht) etwas macht, das selbstständig Werkzeuge nutzen
kann. Konkret ist ein Harness eine Schleife:

```
1. LLM mit der bisherigen Konversation UND der Liste verfügbarer Tools aufrufen
2. Antwort ansehen:
   - enthält sie einen Tool-Aufruf?  -> Tool ausführen, Ergebnis anhängen, zurück zu 1.
   - enthält sie nur Text?           -> fertig, Text als Antwort zurückgeben
```

Das ist buchstäblich der komplette Trick hinter "einem Agenten". Kein
Sprachmodell kann von sich aus eine Datenbank abfragen oder eine Datei
lesen – es kann nur vorschlagen, *dass* und *wie* es das gerne täte
(einen "Tool-Aufruf" formulieren). Der Harness ist der Teil außerhalb des
Modells, der diesen Vorschlag ernst nimmt, das Tool wirklich ausführt,
und dem Modell das Ergebnis zurückgibt, damit es weitermachen kann.

`harness.py` in diesem Ordner ist genau das – bewusst auf ca. 100 Zeilen
reduziert, damit man die komplette Schleife an einem Stück lesen kann.

## Abgrenzung: Harness vs. LLM vs. MCP-Client vs. Agent

Diese vier Begriffe werden im Alltag oft durcheinandergeworfen. An
diesem einen Skript lassen sie sich sauber trennen:

| Begriff | Was es hier ist | Zeile/Funktion in `harness.py` |
|---|---|---|
| **LLM** | das Sprachmodell selbst – bekommt Text+Tools rein, gibt Text oder einen Tool-Aufruf-Wunsch zurück | läuft *außerhalb* dieser Datei (in LM Studio) |
| **MCP-Client** | die schmale Komponente, die die Verbindung zu *einem* MCP-Server verwaltet | `ClientSession`, `stdio_client` – der "Verbindungsstecker" |
| **Harness** | die Schleife, die LLM-Aufruf und Tool-Ausführung so lange abwechselt, bis das LLM fertig ist | die `for step in range(...)`-Schleife in `run_harness()` |
| **Agent** | der *funktionale* Gesamtbegriff für "System, das mehrschrittig auf ein Ziel hinarbeitet" – trifft auf den Harness + LLM + Tools zusammen zu, ist aber keine einzelne Code-Komponente | die Kombination aus allem oben |

Vergleich zu dem, was ihr schon kennt: **Claude Desktop enthält genau
diese vier Teile auch** – nur nicht als 100-Zeilen-Skript, sondern als
Produkt mit Oberfläche. Der `db_agent`/`orchestrator_agent` aus dem
A2A-Teil braucht dagegen (in der aktuellen, einfachen Umsetzung) *keinen*
Harness, weil er kein LLM einbindet – er entscheidet über Regex/feste
Logik, nicht über ein Sprachmodell. Ein A2A-Agent *könnte* intern einen
Harness wie diesen einbauen, um selbst ein LLM zu nutzen (siehe der
Hinweis dazu weiter oben im MCP-vs-A2A-Kapitel dieses Projekts).

## Setup

```bash
pip install -r requirements.txt
# UND die Abhängigkeiten des MCP-Servers, da der Harness ihn als
# Subprozess startet:
pip install -r ../../MCPLokalClaudDesktop/requirements.txt
```

In LM Studio ein **Tool-Calling-fähiges** Modell laden (z. B. Llama 3.1+,
Qwen2.5+) und den lokalen Server starten ("Local Server" → Start).
Nicht jedes lokale Modell unterstützt Tool-Calling zuverlässig – das
steht meist in der Modellbeschreibung in LM Studio.

```bash
python3 harness.py "Wie viele Messungen mit Label 'schlecht' gibt es?"
```

Der Harness gibt bei jedem Schritt aus, was er tut (`[Harness] ...`) –
das macht die Schleife auch beim Zusehen nachvollziehbar.

## Exkurs: API-Key

Dieses Skript läuft standardmäßig gegen LM Studio – ein **lokales**
Modell, **ohne API-Key**, weil nichts das Internet verlässt. Der
`HARNESS_LLM_API_KEY`-Umgebungsvariable ist trotzdem vorgesehen, weil sie
den Unterschied zu Cloud-LLMs (z. B. der Anthropic- oder OpenAI-API)
zeigt: dort ersetzt ein **API-Key** – ein geheimes, dem eigenen Konto
zugeordnetes Passwort – die Notwendigkeit, dass der Anbieter weiß, wer
die Anfrage stellt und wer sie bezahlt. Der Harness-Code selbst (die
Schleife) bliebe bei einem Wechsel auf eine Cloud-API praktisch
identisch – nur `LLM_BASE_URL`, das Anfrageformat für die Autorisierung
und ggf. das exakte Response-Format ändern sich. Das lohnt sich als
Merksatz: **der Harness ist API-unabhängig, nur die Anbindung ans
konkrete LLM wechselt.**

## Bekannte Einschränkungen

- **Nur ein MCP-Server.** Ein "echter" Harness (wie der in Claude
  Desktop) verbindet sich mit *mehreren* MCP-Servern gleichzeitig und
  bietet dem LLM die Tools aller zusammen an. Hier bewusst auf einen
  Server reduziert, um die Schleife nicht zu verschachteln.
- **Kein A2A/LAP.** Dieser Harness kennt nur MCP-Tools. Ein Ausbau, bei
  dem das LLM auch A2A-Tasks an den `db_agent`/`orchestrator_agent`
  delegieren kann, wäre der nächste logische Schritt – bräuchte aber
  eigene "Tool-Definitionen", die intern einen A2A-Aufruf statt eines
  MCP-Aufrufs ausführen.
- **LLM-Hälfte in dieser Umgebung ungetestet.** Der komplette
  MCP-Verbindungsteil (Tool-Discovery, Tool-Ausführung, auch der
  Fehlerfall bei nicht erreichbarer Datenbank) wurde gegen den echten
  `mcpserver.py` verifiziert. Für den Test gegen ein echtes LLM fehlte in
  dieser Umgebung ein laufender LM-Studio-Server. Das Anfrageformat folgt
  der dokumentierten OpenAI-kompatiblen Tool-Calling-Konvention; beim
  ersten echten Testlauf mit eurem Modell die Konsolenausgabe genau
  beobachten.
- **Kein Gedächtnis über einen Aufruf hinaus.** Jeder `harness.py`-Aufruf
  startet mit einer leeren Konversation. Für einen Chat-Verlauf müsste
  `messages` zwischen Aufrufen gespeichert werden (z. B. wie die
  Chat-Tabs im Leitstand-Dashboard das in-memory im Browser tun).
