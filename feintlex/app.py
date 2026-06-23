from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from feintlex import APP_NAME, __version__
from feintlex.config import get_settings
from feintlex.db import init_db
from feintlex.logging_config import configure_logging
from feintlex.routes import autopsy, content, health, lessons, progress, vocabulary, writing


LOGGER = logging.getLogger("feintlex.app")


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        settings = get_settings()
        configure_logging(settings)
        init_db(settings)
        LOGGER.info("startup", extra={"environment": settings.env})
        yield

    application = FastAPI(
        title=APP_NAME,
        version=__version__,
        description="Local-first FeintAI language intelligence trainer.",
        lifespan=lifespan,
    )

    application.include_router(health.router)
    application.include_router(content.router)
    application.include_router(lessons.router)
    application.include_router(autopsy.router)
    application.include_router(vocabulary.router)
    application.include_router(writing.router)
    application.include_router(progress.router)
    return application


app = create_app()
