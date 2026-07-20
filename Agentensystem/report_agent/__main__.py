"""
Startet den Report-Agent als A2A-Server unter Port 9201.
Agent Card: http://localhost:9201/.well-known/agent-card.json

Start:  python -m report_agent
"""
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from report_agent.agent_executor import BerichtAgentExecutor

skill = AgentSkill(
    id="bericht_erstellen",
    name="Bericht erstellen",
    description="Formuliert aus einem Produktionsereignis eine Meldung.",
    tags=["bericht", "kommunikation"],
    examples=["Vorausschauende Wartung an Station S04 durchgeführt."],
)

agent_card = AgentCard(
    name="Report-Agent",
    description="Formuliert Meldungen zu Wartungs- und Nachschubereignissen.",
    url="http://localhost:9201/",
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[skill],
)

request_handler = DefaultRequestHandler(
    agent_executor=BerichtAgentExecutor(),
    task_store=InMemoryTaskStore(),
)

app = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)

if __name__ == "__main__":
    uvicorn.run(app.build(), host="0.0.0.0", port=9201)
