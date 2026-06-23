from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from feintlex.db import get_session
from feintlex.services.writing_coach import submit_writing


router = APIRouter()


class WritingSubmitRequest(BaseModel):
    text: str = Field(min_length=1)
    related_lesson_id: int | None = None


@router.post("/writing/submit")
def writing_submit_route(payload: WritingSubmitRequest, session: Session = Depends(get_session)):
    try:
        return submit_writing(session, payload.text, related_lesson_id=payload.related_lesson_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
