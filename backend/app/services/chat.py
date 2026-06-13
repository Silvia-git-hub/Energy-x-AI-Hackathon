import json
import logging
from typing import AsyncIterator

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a concise solar energy trading analyst for the German and Austrian EPEX spot market.

The dashboard shows the following live values — these are the only numbers you may reference:

- **Signal**: the overall trade signal (STRONG BUY / BUY / HOLD / SELL / STRONG SELL)
- **Solar Index**: site quality score out of 100
- **7d Est.**: 7-day generation forecast in kWh
- **System size**: installed capacity in kWp
- **Skill**: DL model accuracy vs persistence baseline (%)
- **Google Solar score** / **PVGIS score** / **Cloud Cover score**: sub-scores 0–100
- **EPEX price**: current day-ahead spot price in €/MWh, plus day high/low
- **Solar grid share** / **Wind grid share**: current % of grid load from each source

Rules:
- The `signal` field is the authoritative trade recommendation computed by the backend algorithm. Always use it exactly as written — never upgrade, downgrade, or override it with your own assessment.
- Maximum 3 short paragraphs. Be direct and specific.
- Lead with the signal value and explain why the visible metrics support it.
- Never mention signal_score, raw scores, or any field not listed above.
- If a value is null it is not available on the dashboard — do not speculate about it.

## Dashboard State
```json
{context_json}
```"""


def _slim_context(ctx: dict) -> dict:
    """Frontend sends a pre-structured trading context — pass it through, drop nulls."""
    return {k: v for k, v in ctx.items() if v is not None}


class SolarChatService:
    async def stream_response(
        self,
        message: str,
        location_context: dict,
    ) -> AsyncIterator[str]:
        context_json = json.dumps(_slim_context(location_context), indent=2)
        system = SYSTEM_PROMPT.format(context_json=context_json)

        payload = {
            "model":  settings.ollama_model,
            "stream": True,
            "messages": [
                {"role": "system",  "content": system},
                {"role": "user",    "content": message},
            ],
        }

        try:
            async with httpx.AsyncClient(
                base_url=settings.ollama_base_url,
                timeout=httpx.Timeout(120.0, connect=5.0),
            ) as client:
                async with client.stream("POST", "/api/chat", json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        text = chunk.get("message", {}).get("content", "")
                        if text:
                            yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"

                        if chunk.get("done"):
                            break

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except httpx.ConnectError:
            msg = f"Cannot reach Ollama at {settings.ollama_base_url} — is it running?"
            logger.error(msg)
            yield f"data: {json.dumps({'type': 'error', 'content': msg})}\n\n"
        except httpx.HTTPStatusError as exc:
            logger.error("Ollama HTTP error: %s", exc)
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"
        except Exception as exc:
            logger.error("Chat service error: %s", exc)
            yield f"data: {json.dumps({'type': 'error', 'content': 'Internal error during chat.'})}\n\n"
