from __future__ import annotations

from fastapi.testclient import TestClient

from feintlex.app import create_app
from feintlex.db import clear_engine_cache


def test_dashboard_assets_are_served(tmp_path, monkeypatch):
    monkeypatch.setenv("FEINTLEX_DB_PATH", str(tmp_path / "dashboard.db"))
    monkeypatch.setenv("FEINTLEX_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("FEINTLEX_ENV", "test")
    clear_engine_cache()

    with TestClient(create_app()) as client:
        dashboard = client.get("/dashboard")
        css = client.get("/static/dashboard.css")
        js = client.get("/static/dashboard.js")

    assert dashboard.status_code == 200
    assert "FeintLex" in dashboard.text
    assert "Source Intake" in dashboard.text
    assert "Interactive AI Coach" in dashboard.text
    assert css.status_code == 200
    assert js.status_code == 200
    assert "TUTOR_DECKS" in js.text
    assert "/tutor/chat" in js.text
    assert "/tutor/mastery" in js.text
    clear_engine_cache()


def test_dashboard_read_endpoints_list_recent_records(tmp_path, monkeypatch):
    monkeypatch.setenv("FEINTLEX_DB_PATH", str(tmp_path / "dashboard-records.db"))
    monkeypatch.setenv("FEINTLEX_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("FEINTLEX_ENV", "test")
    clear_engine_cache()

    with TestClient(create_app()) as client:
        content = client.post(
            "/content/import",
            json={
                "text": "El equipo analiza alertas porque necesita responder rapido.",
                "source_type": "pasted_text",
                "topic_tags": ["cybersecurity"],
            },
        )
        lesson = client.post("/lessons/generate", json={"content_id": content.json()["id"]})
        content_list = client.get("/content")
        lesson_list = client.get("/lessons")
        export = client.post(f"/exports/lesson/{lesson.json()['id']}")
        export_list = client.get("/exports")

    assert content.status_code == 200
    assert lesson.status_code == 200
    assert content_list.status_code == 200
    assert content_list.json()[0]["source_type"] == "pasted_text"
    assert lesson_list.status_code == 200
    assert lesson_list.json()[0]["title"] == "Cybersecurity Reading Drill"
    assert export.status_code == 200
    assert export_list.status_code == 200
    assert export_list.json()[0]["format"] == "markdown"
    clear_engine_cache()
