from __future__ import annotations

from pathlib import Path

from feintlex.services.content_importer import import_content
from feintlex.services.exports import export_lesson_to_markdown
from feintlex.services.lesson_generator import generate_lesson
from feintlex.services.sentence_autopsy import persist_autopsy


def test_markdown_export_writes_lesson_without_overwriting(isolated_session):
    content = import_content(
        isolated_session,
        "La selección controla el balón y crea oportunidades. El entrenador analiza el ritmo del partido.",
        topic_tags=["soccer"],
    )
    lesson = generate_lesson(isolated_session, content.id)
    persist_autopsy(isolated_session, lesson.sentence_breakdown_candidates[0], lesson_id=lesson.id)

    first = export_lesson_to_markdown(isolated_session, lesson.id)
    second = export_lesson_to_markdown(isolated_session, lesson.id)

    first_path = Path(first.path)
    second_path = Path(second.path)
    assert first_path.exists()
    assert second_path.exists()
    assert first_path != second_path
    markdown = first_path.read_text(encoding="utf-8")
    assert "# Soccer Reading Drill" in markdown
    assert "## Key Vocabulary" in markdown
    assert "## Sentence Autopsies" in markdown
