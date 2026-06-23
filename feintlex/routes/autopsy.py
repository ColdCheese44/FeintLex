from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from feintlex.db import get_session
from feintlex.services.sentence_autopsy import persist_autopsy


router = APIRouter()


class AutopsyRequest(BaseModel):
    sentence: str = Field(min_length=1)
    lesson_id: int | None = None


@router.post("/autopsy")
def autopsy_route(payload: AutopsyRequest, session: Session = Depends(get_session)):
    try:
        return persist_autopsy(session, payload.sentence, lesson_id=payload.lesson_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
