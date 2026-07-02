from __future__ import annotations

from fastapi.testclient import TestClient

from feintlex.app import create_app
from feintlex.db import clear_engine_cache
from feintlex.services.hq import activity_streak, build_hq_status, compute_xp, rank_for_xp


def test_rank_ladder_boundaries():
    assert rank_for_xp(0)["rank"] == "Recruit"
    assert rank_for_xp(99)["rank"] == "Recruit"
    assert rank_for_xp(100)["rank"] == "Field Trainee"
    assert rank_for_xp(100)["next_rank"] == "Signal Analyst"
    top = rank_for_xp(999999)
    assert top["rank"] == "Spymaster"
    assert top["next_rank"] is None
    assert top["rank_progress"] == 1.0


def test_rank_progress_is_fractional():
    # Halfway between Field Trainee (100) and Signal Analyst (300).
    assert abs(rank_for_xp(200)["rank_progress"] - 0.5) < 0.01


def test_xp_and_streak_reflect_activity(tmp_path, monkeypatch):
    monkeypatch.setenv("FEINTLEX_DB_PATH", str(tmp_path / "hq.db"))
    monkeypatch.setenv("FEINTLEX_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("FEINTLEX_ENV", "test")
    clear_engine_cache()

    with TestClient(create_app()) as client:
        before = client.get("/progress/hq").json()
        assert before["xp"] == 0
        assert before["rank"] == "Recruit"
        assert before["streak_days"] == 0
        assert before["active_today"] is False

        content = client.post(
            "/content/import",
            json={
                "text": "El analista revisa alertas porque el equipo detecta actividad sospechosa.",
                "source_type": "pasted_text",
                "topic_tags": ["cybersecurity"],
            },
        )
        client.post("/lessons/generate", json={"content_id": content.json()["id"]})
        client.post("/autopsy", json={"sentence": "El equipo analiza el partido."})
        client.post("/writing/submit", json={"text": "El equipo gana porque practica."})
        client.post("/tutor/chat", json={"message": "hola"})

        after = client.get("/progress/hq").json()
        assert after["xp"] > 0
        # 1 lesson (25) + 1 autopsy (10) + 1 writing (15) + 1 chat (2) minimum.
        assert after["xp"] >= 52
        assert after["active_today"] is True
        assert after["streak_days"] == 1
        assert after["xp_breakdown"]["lessons"] == 25
    clear_engine_cache()


def test_xp_breakdown_totals(isolated_session):
    breakdown = compute_xp(isolated_session)
    assert breakdown["total"] == sum(value for key, value in breakdown.items() if key != "total")
    streak = activity_streak(isolated_session)
    assert streak["streak_days"] == 0
    status = build_hq_status(isolated_session)
    assert status["rank"] == "Recruit"
