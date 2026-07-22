"""
Minimaler Agent-Harness - die Schleife, die aus einem rohen LLM einen
Agenten macht. Siehe README.md fuer die didaktische Einordnung ("Was ist
ein Harness, und wie unterscheidet er sich vom LLM, vom MCP-Client und
vom Agenten selbst?").

Dieses Skript IST buchstaeblich das, was Claude Desktop (oder jeder
andere MCP-Host) intern tut, nur transparent gemacht:
  1. Den MCP-Server als Subprozess starten und seine Tools abfragen
     (das ist der "MCP-Client"-Teil, siehe mcp_tool_to_openai_format).
  2. Diese Tools dem LLM bei jedem Aufruf mit anbieten.
  3. Wenn das LLM einen Tool-Aufruf zurueckgibt: das Tool tatsaechlich
     ueber die MCP-Session ausfuehren, das Ergebnis zurueck an das LLM
     geben.
  4. Wiederholen, bis das LLM eine Antwort ohne weiteren Tool-Aufruf
     liefert (oder ein Sicherheitslimit erreicht ist).

Getestet: der MCP-Verbindungsteil (Tool-Discovery, Tool-Aufruf, inkl.
Fehlerfall bei nicht erreichbarer Datenbank) wurde gegen den echten
../../MCPLokalClaudDesktop/mcpserver.py verifiziert. Der LLM-Teil braucht
einen laufenden, Tool-Calling-faehigen lokalen Server (siehe README) und
konnte in dieser Umgebung nicht end-to-end mitgetestet werden - das
Anfrage-/Antwortformat folgt der dokumentierten OpenAI-kompatiblen
Tool-Calling-Konvention, die LM Studio fuer entsprechend faehige Modelle
unterstuetzt.

Start:  python3 harness.py "Welche Tabellen gibt es in der Datenbank?"
"""
import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

LLM_BASE_URL = os.environ.get("HARNESS_LLM_URL", "http://localhost:1234")
LLM_MODEL = os.environ.get("HARNESS_LLM_MODEL", "local-model")
LLM_API_KEY = os.environ.get("HARNESS_LLM_API_KEY")  # optional, siehe README "API-Key"
MAX_STEPS = int(os.environ.get("HARNESS_MAX_STEPS", "8"))

# Pfad zum bestehenden MCP-Server relativ zu dieser Datei berechnen, damit
# der Harness unabhaengig vom Clone-Pfad des Repos funktioniert.
MCP_SERVER_PATH = (
    Path(__file__).resolve().parent.parent.parent / "MCPLokalClaudDesktop" / "mcpserver.py"
)

SYSTEM_PROMPT = (
    "Du bist ein hilfreicher Assistent fuer das Datenkrake-Projekt einer "
    "Berufsschule. Nutze die verfuegbaren Werkzeuge, wenn eine Frage "
    "Datenbankzugriff auf die Audio-Spektrum-Messungen braucht. "
    "Antworte sonst direkt und knapp auf Deutsch."
)


def mcp_tool_to_openai_format(tool) -> dict:
    """Wandelt ein MCP-Tool-Schema in das OpenAI-kompatible Tool-Format
    um, das LM Studio (und die meisten anderen LLM-APIs) fuer
    Tool-Calling erwarten. Das MCP-inputSchema ist bereits ein normales
    JSON-Schema - es muss nur in die passende Huelle verpackt werden."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


async def call_llm(http: httpx.AsyncClient, messages: list, tools: list) -> dict:
    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    response = await http.post(
        f"{LLM_BASE_URL}/v1/chat/completions",
        headers=headers,
        json={
            "model": LLM_MODEL,
            "messages": messages,
            "tools": tools,
            "temperature": 0.3,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


async def run_harness(user_message: str) -> str:
    params = StdioServerParameters(command=sys.executable, args=[str(MCP_SERVER_PATH)])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            mcp_tools = (await session.list_tools()).tools
            openai_tools = [mcp_tool_to_openai_format(t) for t in mcp_tools]
            print(f"[Harness] {len(openai_tools)} MCP-Tools geladen: "
                  f"{[t.name for t in mcp_tools]}")

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ]

            async with httpx.AsyncClient() as http:
                for step in range(1, MAX_STEPS + 1):
                    print(f"\n[Harness] Schritt {step}: rufe LLM auf...")
                    response = await call_llm(http, messages, openai_tools)
                    message = response["choices"][0]["message"]
                    messages.append(message)

                    tool_calls = message.get("tool_calls")
                    if not tool_calls:
                        print("[Harness] Keine weiteren Tool-Aufrufe - fertig.")
                        return message.get("content", "")

                    for call in tool_calls:
                        name = call["function"]["name"]
                        try:
                            args = json.loads(call["function"]["arguments"] or "{}")
                        except json.JSONDecodeError:
                            args = {}
                        print(f"[Harness]   -> Tool-Aufruf: {name}({args})")

                        result = await session.call_tool(name, args)
                        text = "\n".join(
                            block.text for block in result.content if block.type == "text"
                        )
                        if result.isError:
                            print(f"[Harness]      Fehler vom Tool: {text}")

                        messages.append({
                            "role": "tool",
                            "tool_call_id": call["id"],
                            "content": text,
                        })

                print("[Harness] Maximale Schrittzahl erreicht, breche ab.")
                return "(Abgebrochen: zu viele Tool-Aufrufe in Folge - moeglicherweise haengt das LLM in einer Schleife.)"


if __name__ == "__main__":
    frage = " ".join(sys.argv[1:]) or "Welche Tabellen gibt es in der Datenbank?"
    antwort = asyncio.run(run_harness(frage))
    print("\n=== Antwort ===")
    print(antwort)
