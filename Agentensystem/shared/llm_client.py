"""
Gemeinsamer, minimaler LLM-Client fuer alle Agenten (Orchestrator, DB-,
Report-, Wartungs-Agent). Spricht ein OpenAI-kompatibles
Chat-Completions-API an - standardmaessig ein lokales LM Studio.

Kennt weder MCP noch A2A noch LAP - reines HTTP, damit jeder Agent ihn
unabhaengig von seinem jeweiligen Protokoll nutzen kann.

Jeder Agent kann seine eigenen Umgebungsvariablen (z. B. REPORT_LLM_URL)
mit Vorrang vor diesen Defaults verwenden - siehe Aufrufe von chat()/
chat_text() mit expliziten base_url/model/api_key/timeout-Parametern.

Wichtig zur Sicherheit: dieser Client trifft NIE selbst
sicherheitsrelevante Entscheidungen (z. B. Safety-Fence-Bestaetigungen
im Wartungs-Agent). Er liefert nur Text oder Tool-Aufruf-Vorschlaege -
was damit gemacht wird, entscheidet weiterhin der jeweilige Agent-Code.
"""
import os

import httpx

DEFAULT_BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:1234")
DEFAULT_MODEL = os.environ.get("LLM_MODEL", "local-model")
DEFAULT_API_KEY = os.environ.get("LLM_API_KEY")
DEFAULT_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "30"))


def ist_aktiviert(env_var: str, default: str = "false") -> bool:
    """Liest einen Umgebungsvariablen-Schalter im ueblichen Format
    ('true'/'1'/'yes'/'on'). Zentral an einer Stelle, damit alle Agenten
    denselben Wahrheitswert-Parser nutzen."""
    return os.environ.get(env_var, default).strip().lower() in {"1", "true", "yes", "on"}


async def chat(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.2,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    timeout: int | None = None,
) -> dict:
    """Ruft /v1/chat/completions auf und gibt die rohe 'message' zurueck
    (dict mit 'content' und ggf. 'tool_calls'). Wirft bei Netzwerk-/
    HTTP-Fehlern - der Aufrufer ist fuer den Fallback zustaendig."""
    headers = {"Content-Type": "application/json"}
    key = api_key if api_key is not None else DEFAULT_API_KEY
    if key:
        headers["Authorization"] = f"Bearer {key}"

    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        payload["tools"] = tools

    async with httpx.AsyncClient(timeout=timeout or DEFAULT_TIMEOUT) as client:
        response = await client.post(
            f"{(base_url or DEFAULT_BASE_URL)}/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    return data["choices"][0]["message"]


async def chat_text(messages: list[dict], **kwargs) -> str:
    """Wie chat(), gibt aber direkt den getrimmten Textinhalt zurueck.
    Wirft ValueError, wenn das LLM keinen Text liefert (z. B. weil es
    stattdessen nur einen Tool-Aufruf vorschlaegt)."""
    message = await chat(messages, **kwargs)
    text = (message.get("content") or "").strip()
    if not text:
        raise ValueError("LLM lieferte keinen Text zurueck")
    return text
