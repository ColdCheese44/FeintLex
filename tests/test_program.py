from __future__ import annotations

from fastapi.testclient import TestClient

from feintlex.app import create_app
from feintlex.db import clear_engine_cache
from feintlex.models import TutorMastery, VocabularyEntry
from feintlex.services.program import build_daily_mission, current_phase, known_signal_count


def test_current_phase_thresholds():
    assert current_phase(0)["name"] == "Foundation"
    assert current_phase(299)["next_threshold"] == 300
    assert current_phase(300)["name"] == "Signal Expansion"
    assert current_phase(1500)["name"] == "Field Immersion"
    final = current_phase(5000)
    assert final["name"] == "Native Operations"
    assert final["next_threshold"] is None


def test_known_signal_count_blends_sources(isolated_session):
    isolated_session.add(TutorMastery(term_id="a:0", term="hola", translation="hello", level=3))
    isolated_session.add(TutorMastery(term_id="a:1", term="pero", translation="but", level=1))
    isolated_session.add(VocabularyEntry(term="equipo", normalized_term="equipo", frequency=4))
    isolated_session.add(VocabularyEntry(term="raro", normalized_term="raro", frequency=1))
    isolated_session.commit()

    # level>=3 mastery (1) + frequency>=3 vocab (1)
    assert known_signal_count(isolated_session) == 2


def test_daily_mission_shape_and_completion(isolated_session):
    program = build_daily_mission(isolated_session)
    assert program["phase"] == 1
    assert program["total"] == 6
    mission_ids = [mission["id"] for mission in program["missions"]]
    assert mission_ids == ["queue", "read", "autopsy", "write", "drill", "listen"]
    # Empty database: queue is clear, nothing else done.
    by_id = {mission["id"]: mission for mission in program["missions"]}
    assert by_id["queue"]["done"] is True
    assert by_id["read"]["done"] is False
    assert by_id["listen"]["manual"] is True


def test_noop_mastery_sync_does_not_count_as_drill_activity(isolated_session):
    from datetime import timedelta

    from sqlmodel import select

    from feintlex.models import utc_now
    from feintlex.services.tutor_chat import sync_mastery

    # Seed a row and age its updated_at to before today.
    sync_mastery(
        isolated_session,
        [{"term_id": "contact:0", "term": "hola", "translation": "hello", "level": 2}],
    )
    row = isolated_session.exec(select(TutorMastery).where(TutorMastery.term_id == "contact:0")).first()
    row.updated_at = utc_now() - timedelta(days=3)
    isolated_session.add(row)
    isolated_session.commit()

    # Re-sync the identical snapshot (what the dashboard does on load).
    sync_mastery(
        isolated_session,
        [{"term_id": "contact:0", "term": "hola", "translation": "hello", "level": 2}],
    )
    program = build_daily_mission(isolated_session)
    drill = next(mission for mission in program["missions"] if mission["id"] == "drill")
    assert drill["done"] is False, "a no-op sync must not mark the drill mission complete"

    # A real level change does count.
    sync_mastery(
        isolated_session,
        [{"term_id": "contact:0", "term": "hola", "translation": "hello", "level": 3}],
    )
    program = build_daily_mission(isolated_session)
    drill = next(mission for mission in program["missions"] if mission["id"] == "drill")
    assert drill["done"] is True


def test_program_route_tracks_todays_activity(tmp_path, monkeypatch):
    monkeypatch.setenv("FEINTLEX_DB_PATH", str(tmp_path / "program.db"))
    monkeypatch.setenv("FEINTLEX_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("FEINTLEX_ENV", "test")
    clear_engine_cache()

    with TestClient(create_app()) as client:
        before = client.get("/program/today").json()
        before_by_id = {mission["id"]: mission for mission in before["missions"]}
        assert before_by_id["read"]["done"] is False
        assert before_by_id["write"]["done"] is False

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
        client.post("/autopsy", json={"sentence": "La defensa presiona cuando el rival avanza."})
        client.post("/writing/submit", json={"text": "El equipo gana porque practica cada semana."})
        client.put(
            "/tutor/mastery",
            json={"items": [{"term_id": "contact:0", "term": "hola", "translation": "hello", "level": 1}]},
        )

        after = client.get("/program/today").json()
        after_by_id = {mission["id"]: mission for mission in after["missions"]}
        assert after_by_id["read"]["done"] is True
        assert after_by_id["autopsy"]["done"] is True
        assert after_by_id["write"]["done"] is True
        assert after_by_id["drill"]["done"] is True
        assert after["completed"] >= 4
    clear_engine_cache()
