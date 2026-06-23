from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from feintlex.db import get_session
from feintlex.models import ExportRecord, Lesson
from feintlex.services.exports import export_lesson_to_markdown
from feintlex.services.lesson_generator import generate_lesson


router = APIRouter()


class LessonGenerateRequest(BaseModel):
    content_id: int


@router.post("/lessons/generate")
def generate_lesson_route(payload: LessonGenerateRequest, session: Session = Depends(get_session)):
    try:
        return generate_lesson(session, payload.content_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/lessons")
def list_lessons_route(limit: int = 20, session: Session = Depends(get_session)):
    limit = max(1, min(limit, 100))
    statement = select(Lesson).order_by(Lesson.created_at.desc()).limit(limit)
    return list(session.exec(statement).all())


@router.get("/lessons/{lesson_id}")
def get_lesson_route(lesson_id: int, session: Session = Depends(get_session)):
    lesson = session.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} was not found.")
    return lesson


@router.post("/exports/lesson/{lesson_id}")
def export_lesson_route(lesson_id: int, session: Session = Depends(get_session)):
    try:
        return export_lesson_to_markdown(session, lesson_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/exports")
def list_exports_route(limit: int = 20, session: Session = Depends(get_session)):
    limit = max(1, min(limit, 100))
    statement = select(ExportRecord).order_by(ExportRecord.created_at.desc()).limit(limit)
    return list(session.exec(statement).all())
