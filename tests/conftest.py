from __future__ import annotations

import pytest
from sqlmodel import Session

from feintlex.config import get_settings
from feintlex.db import clear_engine_cache, get_engine, init_db


@pytest.fixture()
def isolated_session(tmp_path, monkeypatch):
    monkeypatch.setenv("FEINTLEX_DB_PATH", str(tmp_path / "feintlex.db"))
    monkeypatch.setenv("FEINTLEX_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("FEINTLEX_ENV", "test")
    clear_engine_cache()
    settings = get_settings()
    init_db(settings)
    with Session(get_engine(settings)) as session:
        yield session
    clear_engine_cache()
