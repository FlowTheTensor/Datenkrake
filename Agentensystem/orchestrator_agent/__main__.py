"""
Startet den Orchestrator-Agent: A2A-Server (Agent Card) UND die
Überwachungsschleife aus monitor.py, parallel im selben Prozess.

Start:  python -m orchestrator_agent
"""
import asyncio

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from orchestrator_agent.agent_executor import OrchestratorAgentExecutor
from orchestrator_agent.monitor import loop as ueberwachungsschleife

skill = AgentSkill(
    id="wartungsstatus_melden",
    name="Wartungsstatus melden",
    description="Meldet Anzahl offener Anomalien auf Anfrage.",
    tags=["wartung"],
    examples=["Wartungsstatus?"],
)

agent_card = AgentCard(
    name="Orchestrator-Agent",
    description="Überwacht die Datenkrake und delegiert Wartung per LAP.",
    url="http://localhost:9200/",
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[skill],
)

request_handler = DefaultRequestHandler(
    agent_executor=OrchestratorAgentExecutor(),
    task_store=InMemoryTaskStore(),
)

app = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)


async def main() -> None:
    config = uvicorn.Config(app.build(), host="0.0.0.0", port=9200, log_level="info")
    server = uvicorn.Server(config)
    await asyncio.gather(server.serve(), ueberwachungsschleife())


if __name__ == "__main__":
    asyncio.run(main())
