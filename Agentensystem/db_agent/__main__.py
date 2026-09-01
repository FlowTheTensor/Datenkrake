"""
Startet den DB-Agent als A2A-Server.
Agent Card: http://localhost:9999/.well-known/agent-card.json

Start:  python -m db_agent
"""
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from starlette.responses import PlainTextResponse

from db_agent.agent_executor import GRAPH, TelemetrieAgentExecutor

skill = AgentSkill(
    id="telemetrie_abfragen",
    name="Telemetrie abfragen",
    description="Liefert offene Akustik-Anomalien und Statistiken der Datenkrake.",
    tags=["telemetrie", "wartung"],
    examples=["Offene Anomalien?", "Statistik"],
)

agent_card = AgentCard(
    name="DB-Agent (Datenkrake)",
    description="Liest Akustik-Telemetrie und Anomalien aus der Datenkrake-MariaDB.",
    url="http://localhost:9999/",
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[skill],
)

request_handler = DefaultRequestHandler(
    agent_executor=TelemetrieAgentExecutor(),
    task_store=InMemoryTaskStore(),
)

app = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)
built_app = app.build()


async def graph_mermaid(request):
    """Mermaid-Quelltext des Entscheidungsgraphen - vom Leitstand-Dashboard
    (Tab "Agenten-Graphen") live abgerufen. Kein CORS-Header gesetzt, siehe
    Hinweis zu den Agent-Cards im Haupt-README."""
    return PlainTextResponse(GRAPH.get_graph().draw_mermaid())


built_app.add_route("/graph/mermaid", graph_mermaid, methods=["GET"])

if __name__ == "__main__":
    uvicorn.run(built_app, host="0.0.0.0", port=9999)
