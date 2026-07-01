from __future__ import annotations

from fastapi.testclient import TestClient

from feintlex.app import create_app
from feintlex.db import clear_engine_cache
from feintlex.services.tutor import generate_tutor_response


def test_tutor_service_generates_autopsy_response():
    response = generate_tutor_response("El equipo analiza alertas porque necesita responder.", action="autopsy")

    assert response["action"] == "autopsy"
    assert response["ai_provider"] == "offline_rule_based"
    assert response["cards"][0]["original"].startswith("El equipo")
    assert response["cards"][0]["connectors"]


def test_tutor_service_generates_quiz_cards():
    response = generate_tutor_response("El analista revisa alertas de seguridad.", action="quiz")

    assert response["action"] == "quiz"
    assert response["cards"]
    assert response["cards"][0]["type"] == "short_answer"


def test_tutor_route_uses_active_lesson_context(tmp_path, monkeypatch):
    monkeypatch.setenv("FEINTLEX_DB_PATH", str(tmp_path / "tutor.db"))
    monkeypatch.setenv("FEINTLEX_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("FEINTLEX_ENV", "test")
    clear_engine_cache()

    with TestClient(create_app()) as client:
        content = client.post(
            "/content/import",
            json={
                "text": "El analista revisa alertas porque el equipo detecta actividad sospechosa.",
                "source_type": "pasted_text",
                "topic_tags": ["cybersecurity"],
            },
        )
        lesson = client.post("/lessons/generate", json={"content_id": content.json()["id"]})
        response = client.post(
            "/tutor/respond",
            json={
                "message": "Explain the pattern.",
                "action": "explain",
                "lesson_id": lesson.json()["id"],
                "selected_term": "alertas = alerts",
                "selected_deck": "Core Verbs",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "explain"
    assert "Cybersecurity Reading Drill" in payload["lesson_context"]
    assert payload["selected_term"] == "alertas = alerts"
    clear_engine_cache()
