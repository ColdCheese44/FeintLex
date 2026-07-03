from __future__ import annotations

from fastapi.testclient import TestClient

from feintlex.app import create_app
from feintlex.db import clear_engine_cache
from feintlex.services.methods import (
    backward_buildup,
    build_constructor_session,
    build_echo_session,
    record_method_results,
)


def test_backward_buildup_grows_from_the_tail():
    chunks = backward_buildup("El equipo necesita responder ahora mismo")
    assert chunks[-1] == "El equipo necesita responder ahora mismo"
    assert len(chunks) >= 2
    # Each chunk is a suffix of the full sentence and grows.
    for earlier, later in zip(chunks, chunks[1:]):
        assert later.endswith(earlier)
    # Short sentences stay whole.
    assert backward_buildup("No entiendo") == ["No entiendo"]


def test_echo_session_uses_graduated_intervals(isolated_session):
    session_plan = build_echo_session(isolated_session, size=4)
    prompts = session_plan["prompts"]
    assert session_plan["method"] == "echo"
    assert session_plan["items"] == 4
    # 1 introduction + 4 recalls per item.
    assert len(prompts) == 4 * 5
    assert prompts[0]["mode"] == "introduce"

    # Every introduction precedes all of that item's recalls, and recalls
    # arrive in graduated order.
    first_seen: dict[str, str] = {}
    recall_counts: dict[str, int] = {}
    for prompt in prompts:
        term = prompt["term_id"]
        if term not in first_seen:
            assert prompt["mode"] == "introduce", "recall arrived before introduction"
            first_seen[term] = prompt["mode"]
        elif prompt["mode"] == "recall":
            recall_counts[term] = recall_counts.get(term, 0) + 1
            assert prompt["recall_index"] == recall_counts[term]
    assert all(count == 4 for count in recall_counts.values())
    # Backward buildup is attached for the reveal.
    assert all(prompt["chunks"] for prompt in prompts)


def test_constructor_session_shape(isolated_session):
    plan = build_constructor_session(isolated_session)
    assert plan["method"] == "constructor"
    types = [step["type"] for step in plan["steps"]]
    assert types[0] == "teach", "session opens with a cognate rule"
    assert "convert" in types
    assert "produce" in types
    assert "build" in types
    # Build steps carry shuffled tiles that reconstruct the answer.
    for step in plan["steps"]:
        if step["type"] == "build":
            assert sorted(step["tiles"]) == sorted(step["answer_es"].split())
        if step["type"] in {"convert", "produce", "build"}:
            assert step["term_id"]
            assert step["answer_es"]


def test_record_method_results_feeds_mastery(isolated_session):
    summary = record_method_results(
        isolated_session,
        method="echo",
        results=[
            {"term_id": "echo:quiero-un-cafe", "es": "Quiero un cafe", "en": "I want a coffee", "correct": True},
            {"term_id": "echo:no-entiendo", "es": "No entiendo", "en": "I don't understand", "correct": False},
        ],
    )
    assert summary["recorded"] == 2
    assert summary["correct"] == 1

    from sqlmodel import select

    from feintlex.models import TutorMastery

    rows = {row.term_id: row for row in isolated_session.exec(select(TutorMastery)).all()}
    assert rows["echo:quiero-un-cafe"].level == 1
    assert rows["echo:quiero-un-cafe"].deck_id == "echo"
    assert rows["echo:no-entiendo"].level == 0
    assert rows["echo:no-entiendo"].seen == 1


def test_method_routes(tmp_path, monkeypatch):
    monkeypatch.setenv("FEINTLEX_DB_PATH", str(tmp_path / "methods.db"))
    monkeypatch.setenv("FEINTLEX_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("FEINTLEX_ENV", "test")
    clear_engine_cache()

    with TestClient(create_app()) as client:
        echo = client.get("/methods/session?method=echo&size=4")
        assert echo.status_code == 200
        assert echo.json()["items"] == 4

        constructor = client.get("/methods/session?method=constructor")
        assert constructor.status_code == 200
        assert constructor.json()["steps"]

        done = client.post(
            "/methods/complete",
            json={
                "method": "constructor",
                "results": [{"term_id": "constructor:rule:cion", "es": "operacion", "en": "operation", "correct": True}],
            },
        )
        assert done.status_code == 200
        assert done.json()["correct"] == 1

        empty = client.post("/methods/complete", json={"method": "echo", "results": []})
        assert empty.status_code == 400

        bad = client.get("/methods/session?method=nonsense")
        assert bad.status_code == 422
    clear_engine_cache()
