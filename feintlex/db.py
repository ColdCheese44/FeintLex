from __future__ import annotations

from collections.abc import Generator
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from feintlex.config import Settings, get_settings


_ENGINES: dict[str, Engine] = {}


def get_engine(settings: Settings | None = None) -> Engine:
    settings = settings or get_settings()
    db_path = settings.resolved_db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    key = str(db_path)
    if key not in _ENGINES:
        _ENGINES[key] = create_engine(
            f"sqlite:///{db_path.as_posix()}",
            connect_args={"check_same_thread": False},
        )
    return _ENGINES[key]


def init_db(settings: Settings | None = None) -> None:
    from feintlex import models  # noqa: F401

    SQLModel.metadata.create_all(get_engine(settings))


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session


def database_status(settings: Settings | None = None) -> str:
    try:
        with Session(get_engine(settings)) as session:
            session.exec(text("select 1")).one()
        return "ok"
    except Exception:
        return "error"


def clear_engine_cache() -> None:
    for engine in _ENGINES.values():
        engine.dispose()
    _ENGINES.clear()
