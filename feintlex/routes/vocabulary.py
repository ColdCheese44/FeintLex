from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from feintlex.db import get_session
from feintlex.models import VocabularyEntry
from feintlex.services.lexicon import LEXICON, PHRASES


router = APIRouter()


@router.get("/vocabulary")
def vocabulary_route(session: Session = Depends(get_session)):
    statement = select(VocabularyEntry).order_by(VocabularyEntry.frequency.desc(), VocabularyEntry.term)
    return list(session.exec(statement).all())


@router.get("/lexicon")
def lexicon_route():
    """Full offline ES->EN lexicon for the dashboard hover-gloss dictionary.

    Keys are normalized (lowercase, accent-free); the frontend normalizes
    hovered words the same way before lookup.
    """
    return {"terms": LEXICON, "phrases": PHRASES}
