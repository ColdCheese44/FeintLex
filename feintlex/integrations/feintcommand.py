from __future__ import annotations

import logging

from feintlex.config import Settings, get_settings


LOGGER = logging.getLogger("feintlex.integrations.feintcommand")


def post_event(event_type: str, payload: dict[str, object], *, settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    if not settings.feintcommand_endpoint:
        LOGGER.info("feintcommand_event_skipped", extra={"event_type": event_type})
        return False
    LOGGER.info("feintcommand_event_ready", extra={"event_type": event_type})
    return False
