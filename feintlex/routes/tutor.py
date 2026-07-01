from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from feintlex.db import get_session
from feintlex.models import Lesson
from feintlex.services.tutor import TutorContext, generate_tutor_response


router = APIRouter()


class TutorRequest(BaseModel):
    message: str = Field(default="")
    action: str | None = None
    lesson_id: int | None = None
    selected_term: str | None = None
    selected_deck: str | None = None


@router.post("/tutor/respond")
def tutor_response_route(payload: TutorRequest, session: Session = Depends(get_session)):
    lesson = None
    if payload.lesson_id is not None:
        lesson = session.get(Lesson, payload.lesson_id)
        if lesson is None:
            raise HTTPException(status_code=404, detail=f"Lesson {payload.lesson_id} was not found.")

    return generate_tutor_response(
        payload.message,
        action=payload.action,
        context=TutorContext(
            lesson=lesson,
            selected_term=payload.selected_term,
            selected_deck=payload.selected_deck,
        ),
    )
