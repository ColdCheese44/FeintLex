from __future__ import annotations

import logging

from feintlex.config import Settings, get_settings


LOGGER = logging.getLogger("feintlex.integrations.discord")


def notify(event_type: str, message: str, *, settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    if not settings.discord_webhook_url:
        LOGGER.info("discord_notification_skipped", extra={"event_type": event_type})
        return False
    LOGGER.info("discord_notification_queued", extra={"event_type": event_type})
    return False
