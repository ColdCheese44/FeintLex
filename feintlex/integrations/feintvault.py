from __future__ import annotations

import logging

from feintlex.config import Settings, get_settings


LOGGER = logging.getLogger("feintlex.integrations.feintvault")


def archive_artifact(artifact_type: str, path: str, *, settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    if not settings.feintvault_endpoint:
        LOGGER.info("feintvault_archive_skipped", extra={"artifact_type": artifact_type})
        return False
    LOGGER.info("feintvault_archive_ready", extra={"artifact_type": artifact_type, "path": path})
    return False
