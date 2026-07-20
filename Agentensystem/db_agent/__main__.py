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

from db_agent.agent_executor import TelemetrieAgentExecutor

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

if __name__ == "__main__":
    uvicorn.run(app.build(), host="0.0.0.0", port=9999)
