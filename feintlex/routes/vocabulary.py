from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from feintlex.db import get_session
from feintlex.models import VocabularyEntry


router = APIRouter()


@router.get("/vocabulary")
def vocabulary_route(session: Session = Depends(get_session)):
    statement = select(VocabularyEntry).order_by(VocabularyEntry.frequency.desc(), VocabularyEntry.term)
    return list(session.exec(statement).all())
