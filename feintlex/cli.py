from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
from sqlmodel import Session

from feintlex import APP_NAME, __version__
from feintlex.config import get_settings
from feintlex.db import database_status, get_engine, init_db
from feintlex.logging_config import configure_logging
from feintlex.services.content_importer import import_content
from feintlex.services.exports import export_lesson_to_markdown
from feintlex.services.lesson_generator import generate_lesson
from feintlex.services.mistake_bank import get_due_mistakes
from feintlex.services.sentence_autopsy import autopsy_sentence


app = typer.Typer(no_args_is_help=True, help="FeintLex local-first language intelligence trainer.")


def bootstrap() -> None:
    settings = get_settings()
    configure_logging(settings)
    init_db(settings)


def print_json(payload: Any) -> None:
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def model_payload(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return dict(model)


@app.command("health")
def health_command() -> None:
    """Print app, environment, and database health."""
    bootstrap()
    settings = get_settings()
    print_json(
        {
            "app": APP_NAME,
            "version": __version__,
            "environment": settings.env,
            "database_status": database_status(settings),
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


@app.command("import-text")
def import_text_command(
    file: str = typer.Option(..., "--file", help="A path to a text file, or direct pasted text."),
    source_type: str = typer.Option("pasted_text", "--source-type"),
    topic_tag: list[str] = typer.Option(None, "--topic-tag", help="Topic tag; repeat for multiple tags."),
) -> None:
    """Import pasted Spanish text or a local text file."""
    bootstrap()
    candidate = Path(file)
    text = candidate.read_text(encoding="utf-8") if candidate.exists() else file
    with Session(get_engine()) as session:
        item = import_content(session, text, source_type=source_type, topic_tags=topic_tag or [])
        print_json(model_payload(item))


@app.command("make-lesson")
def make_lesson_command(content_id: int = typer.Option(..., "--content-id")) -> None:
    """Generate a deterministic MVP lesson from imported content."""
    bootstrap()
    with Session(get_engine()) as session:
        lesson = generate_lesson(session, content_id)
        print_json(model_payload(lesson))


@app.command("autopsy")
def autopsy_command(sentence: str = typer.Option(..., "--sentence")) -> None:
    """Run rule-based sentence autopsy on a Spanish sentence."""
    bootstrap()
    print_json(autopsy_sentence(sentence))


@app.command("export-lesson")
def export_lesson_command(lesson_id: int = typer.Option(..., "--lesson-id")) -> None:
    """Export a lesson to Markdown."""
    bootstrap()
    with Session(get_engine()) as session:
        record = export_lesson_to_markdown(session, lesson_id)
        print_json(model_payload(record))


@app.command("review-due")
def review_due_command() -> None:
    """List mistake-bank items due for review."""
    bootstrap()
    with Session(get_engine()) as session:
        mistakes = [model_payload(item) for item in get_due_mistakes(session)]
        print_json({"mistakes": mistakes})


if __name__ == "__main__":
    app()
