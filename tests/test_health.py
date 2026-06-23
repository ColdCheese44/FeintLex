from __future__ import annotations

from fastapi.testclient import TestClient

from feintlex.app import create_app
from feintlex.db import clear_engine_cache


def test_health_route_reports_database_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("FEINTLEX_DB_PATH", str(tmp_path / "health.db"))
    monkeypatch.setenv("FEINTLEX_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("FEINTLEX_ENV", "test")
    clear_engine_cache()

    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["app"] == "FeintLex"
    assert payload["environment"] == "test"
    assert payload["database_status"] == "ok"
    clear_engine_cache()
