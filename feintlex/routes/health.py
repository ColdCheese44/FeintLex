from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from feintlex import APP_NAME, __version__
from feintlex.config import get_settings
from feintlex.db import database_status


router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "app": APP_NAME,
        "version": __version__,
        "environment": settings.env,
        "database_status": database_status(settings),
        "timestamp": datetime.now(UTC).isoformat(),
    }
