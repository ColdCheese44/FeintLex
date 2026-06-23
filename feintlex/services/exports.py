from __future__ import annotations

import logging
import re
from pathlib import Path

from sqlmodel import Session, select

from feintlex.config import Settings, get_settings
from feintlex.models import ExportRecord, Lesson, SentenceAutopsy


LOGGER = logging.getLogger("feintlex.exports")


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:60] or "lesson"


def unique_path(directory: Path, filename: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    counter = 2
    while True:
        next_candidate = directory / f"{stem}-{counter}{suffix}"
        if not next_candidate.exists():
            return next_candidate
        counter += 1


def lesson_to_markdown(session: Session, lesson: Lesson) -> str:
    autopsies = session.exec(
        select(SentenceAutopsy).where(SentenceAutopsy.lesson_id == lesson.id).order_by(SentenceAutopsy.created_at)
    ).all()
    lines = [
        f"# {lesson.title}",
        "",
        f"- Source language: {lesson.source_language}",
        f"- Target language: {lesson.target_language}",
        "",
        "## English Summary",
        lesson.english_summary,
        "",
        "## Spanish Summary",
        lesson.spanish_summary,
        "",
        "## Key Vocabulary",
    ]
    for item in lesson.key_vocabulary:
        lines.append(f"- {item['term']} ({item['frequency']})")
    lines.extend(["", "## Grammar Points"])
    for item in lesson.grammar_points:
        lines.append(f"- {item}")
    lines.extend(["", "## Sentence Autopsy Candidates"])
    for sentence in lesson.sentence_breakdown_candidates:
        lines.append(f"- {sentence}")
    if autopsies:
        lines.extend(["", "## Sentence Autopsies"])
        for autopsy in autopsies:
            lines.extend(
                [
                    f"### {autopsy.original}",
                    f"- Literal: {autopsy.literal_translation}",
                    f"- Natural: {autopsy.natural_translation}",
                    f"- Pattern: {autopsy.pattern}",
                    f"- Practice: {autopsy.practice_prompt}",
                ]
            )
    lines.extend(["", "## Quiz"])
    for question in lesson.quiz.get("multiple_choice", []):
        lines.append(f"- {question['question']} Answer: {question['answer']}")
    for question in lesson.quiz.get("short_answer", []):
        lines.append(f"- {question['question']}")
    lines.extend(["", "## Writing Prompt", lesson.writing_prompt, "", "## Review Items"])
    for item in lesson.review_items:
        lines.append(f"- [{item['type']}] {item['prompt']}")
    lines.append("")
    return "\n".join(lines)


def export_lesson_to_markdown(
    session: Session,
    lesson_id: int,
    *,
    settings: Settings | None = None,
) -> ExportRecord:
    settings = settings or get_settings()
    lesson = session.get(Lesson, lesson_id)
    if lesson is None:
        raise ValueError(f"Lesson {lesson_id} was not found.")
    filename = f"{slugify(lesson.title)}-{lesson.id}.md"
    path = unique_path(settings.resolved_export_dir, filename)
    path.write_text(lesson_to_markdown(session, lesson), encoding="utf-8")
    record = ExportRecord(lesson_id=lesson.id, path=str(path), format="markdown")
    session.add(record)
    session.commit()
    session.refresh(record)
    LOGGER.info("lesson_exported", extra={"lesson_id": lesson.id, "export_id": record.id})
    return record
