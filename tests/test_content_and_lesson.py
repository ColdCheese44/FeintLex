from __future__ import annotations

from sqlmodel import select

from feintlex.models import ReviewItem, VocabularyEntry
from feintlex.services.content_importer import import_content
from feintlex.services.lesson_generator import generate_lesson


SPANISH_TEXT = (
    "El analista revisa alertas de seguridad porque el equipo detecta actividad sospechosa. "
    "Después, el equipo escribe un informe claro para explicar el riesgo."
)


def test_content_import_stores_pasted_text(isolated_session):
    item = import_content(isolated_session, SPANISH_TEXT, topic_tags=["cybersecurity", "investigation"])
    assert item.id is not None
    assert item.source_type == "pasted_text"
    assert item.topic_tags == ["cybersecurity", "investigation"]


def test_lesson_generation_fallback_creates_structured_lesson(isolated_session):
    content = import_content(isolated_session, SPANISH_TEXT, topic_tags=["cybersecurity"])
    lesson = generate_lesson(isolated_session, content.id)

    assert lesson.id is not None
    assert lesson.title == "Cybersecurity Reading Drill"
    assert lesson.english_summary.startswith("Rule-based MVP summary")
    assert lesson.key_vocabulary
    assert lesson.grammar_points
    assert lesson.sentence_breakdown_candidates
    assert lesson.quiz["multiple_choice"]
    assert len(isolated_session.exec(select(VocabularyEntry)).all()) > 0
    assert len(isolated_session.exec(select(ReviewItem)).all()) > 0
