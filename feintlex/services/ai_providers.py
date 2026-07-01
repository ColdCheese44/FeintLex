from __future__ import annotations

"""Optional local AI providers for tutor chat.

FeintLex is offline-first: the rule-based tutor always works and no
provider is ever required. If FEINTLEX_AI_PROVIDER=ollama is set and a
local Ollama server is running, chat replies are enriched by the local
model. Any failure silently falls back to the rule-based engine.

No paid APIs. No new dependencies (stdlib urllib only).
"""

import json
import logging
import urllib.error
import urllib.request

from feintlex.config import Settings


LOGGER = logging.getLogger("feintlex.ai_providers")

_TUTOR_SYSTEM_PROMPT = (
    "You are FeintLex, a tactical Spanish tutor for an English speaker. "
    "Be concise and practical: explain the pattern, give 1-3 example sentences "
    "in Spanish with English translations, and end with one short practice task. "
    "Never invent vocabulary lists longer than 5 items."
)


def provider_enabled(settings: Settings) -> bool:
    return settings.ai_provider.strip().lower() == "ollama"


def generate_ai_reply(prompt: str, settings: Settings, *, timeout: float = 20.0) -> tuple[str, str] | None:
    """Try the configured local provider. Returns (reply, provider_tag) or None."""
    if not provider_enabled(settings):
        return None

    url = settings.ollama_url.rstrip("/") + "/api/generate"
    payload = json.dumps(
        {
            "model": settings.ollama_model,
            "system": _TUTOR_SYSTEM_PROMPT,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.4, "num_predict": 500},
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        reply = str(body.get("response", "")).strip()
        if reply:
            return reply, f"ollama:{settings.ollama_model}"
        return None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError) as exc:
        LOGGER.info("local_ai_provider_unavailable", extra={"error": str(exc)})
        return None
