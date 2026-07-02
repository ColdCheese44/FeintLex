from __future__ import annotations

from fastapi.testclient import TestClient

from feintlex.app import create_app
from feintlex.db import clear_engine_cache
from feintlex.models import ReviewItem, TutorMastery
from feintlex.services.mistake_bank import create_mistake
from feintlex.services.review_queue import build_review_queue, complete_review


def _seed(session):
    create_mistake(
        session,
        mistake_type="gender_agreement",
        original_input="la sistema",
        correction="el sistema",
        explanation="'sistema' takes el.",
    )
    session.add(ReviewItem(item_type="vocabulary", prompt="Recall 'amenaza'.", answer="threat"))
    session.add(
        TutorMastery(term_id="contact:0", deck_id="contact", term="hola", translation="hello", level=1)
    )
    session.commit()


def test_queue_blends_all_sources(isolated_session):
    _seed(isolated_session)
    queue = build_review_queue(isolated_session)
    kinds = [item["kind"] for item in queue]
    assert "mistake" in kinds
    assert "review_item" in kinds
    assert "term" in kinds
    # Mistakes outrank review items, which outrank weak terms.
    assert kinds.index("mistake") < kinds.index("review_item") < kinds.index("term")
    term_item = next(item for item in queue if item["kind"] == "term")
    assert term_item["speak"] == "hola"
    assert term_item["answer"] == "hello"


def test_complete_review_transitions(isolated_session):
    _seed(isolated_session)
    queue = build_review_queue(isolated_session)

    mistake = next(item for item in queue if item["kind"] == "mistake")
    result = complete_review(isolated_session, kind="mistake", item_id=mistake["id"], result="got")
    assert result["status"] == "learning"

    review_item = next(item for item in queue if item["kind"] == "review_item")
    result = complete_review(isolated_session, kind="review_item", item_id=review_item["id"], result="got")
    assert result["status"] == "done"

    term = next(item for item in queue if item["kind"] == "term")
    result = complete_review(isolated_session, kind="term", item_id=term["id"], result="got")
    assert result["level"] == 2
    result = complete_review(isolated_session, kind="term", item_id=term["id"], result="missed")
    assert result["level"] == 1

    # Graded items leave the queue (mistake rescheduled, review item done).
    remaining = build_review_queue(isolated_session)
    assert all(item["kind"] == "term" for item in remaining)


def test_complete_review_rejects_bad_input(isolated_session):
    try:
        complete_review(isolated_session, kind="nonsense", item_id=1, result="got")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def _client(tmp_path, monkeypatch, name):
    monkeypatch.setenv("FEINTLEX_DB_PATH", str(tmp_path / f"{name}.db"))
    monkeypatch.setenv("FEINTLEX_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("FEINTLEX_ENV", "test")
    clear_engine_cache()
    return TestClient(create_app())


def test_review_queue_routes(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch, "queue-routes") as client:
        # Writing submission with issues feeds the mistake bank -> queue.
        writing = client.post(
            "/writing/submit",
            json={"text": "donde esta el problema? la sistema falla."},
        )
        assert writing.status_code == 200
        assert writing.json()["issues"], "structured issues should be stored"

        queue = client.get("/review/queue").json()
        assert queue, "queue should contain mistakes from the writing submission"
        first = queue[0]
        assert first["kind"] == "mistake"

        done = client.post(
            "/review/complete",
            json={"kind": first["kind"], "id": first["id"], "result": "got"},
        )
        assert done.status_code == 200

        bad = client.post("/review/complete", json={"kind": "mistake", "id": 99999, "result": "got"})
        assert bad.status_code == 400
    clear_engine_cache()


def test_progress_summary_route(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch, "summary") as client:
        content = client.post(
            "/content/import",
            json={"text": "El analista revisa alertas porque el equipo detecta actividad sospechosa.", "source_type": "pasted_text", "topic_tags": ["cybersecurity"]},
        )
        client.post("/lessons/generate", json={"content_id": content.json()["id"]})
        client.post("/tutor/chat", json={"message": "hola"})
        client.put(
            "/tutor/mastery",
            json={"items": [{"term_id": "contact:0", "term": "hola", "translation": "hello", "level": 5}]},
        )

        summary = client.get("/progress/summary").json()
        assert summary["lessons"] == 1
        assert summary["vocabulary_terms"] > 0
        assert summary["chat_messages"] == 2
        assert summary["review_items_due"] > 0
        assert summary["mastery_tracked"] == 1
        assert summary["mastery_locked"] == 1
    clear_engine_cache()
