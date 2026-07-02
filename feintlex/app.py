from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from feintlex import APP_NAME, __version__
from feintlex.config import get_settings
from feintlex.db import init_db
from feintlex.logging_config import configure_logging
from feintlex.routes import autopsy, content, health, lessons, program, progress, tutor, vocabulary, writing


LOGGER = logging.getLogger("feintlex.app")
STATIC_DIR = Path(__file__).resolve().parent / "static"


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

    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @application.get("/")
    @application.get("/dashboard")
    def dashboard() -> HTMLResponse:
        # Cache-bust static assets with their modification time so the
        # browser always picks up dashboard changes on reload.
        html = (STATIC_DIR / "dashboard.html").read_text(encoding="utf-8")
        stamp = int(max((STATIC_DIR / name).stat().st_mtime for name in ("dashboard.js", "dashboard.css")))
        html = html.replace('href="/static/dashboard.css"', f'href="/static/dashboard.css?v={stamp}"')
        html = html.replace('src="/static/dashboard.js"', f'src="/static/dashboard.js?v={stamp}"')
        return HTMLResponse(html)

    application.include_router(health.router)
    application.include_router(content.router)
    application.include_router(lessons.router)
    application.include_router(autopsy.router)
    application.include_router(vocabulary.router)
    application.include_router(writing.router)
    application.include_router(progress.router)
    application.include_router(program.router)
    application.include_router(tutor.router)
    return application


app = create_app()
