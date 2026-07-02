from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from feintlex.db import get_session
from feintlex.models import VocabularyEntry
from feintlex.services.lexicon import CATEGORIES, LEXICON, PHRASES, derived_forms, library_stats


router = APIRouter()


@router.get("/vocabulary")
def vocabulary_route(session: Session = Depends(get_session)):
    statement = select(VocabularyEntry).order_by(VocabularyEntry.frequency.desc(), VocabularyEntry.term)
    return list(session.exec(statement).all())


@router.get("/lexicon")
def lexicon_route():
    """Full offline ES->EN library for hover glosses and the Library tab.

    Keys are normalized (lowercase, accent-free); the frontend normalizes
    hovered words the same way before lookup. `derived` holds conjugated
    verb forms auto-generated from every verb in the lexicon.
    """
    return {
        "terms": LEXICON,
        "phrases": PHRASES,
        "derived": derived_forms(),
        "categories": {name: sorted(entries.keys()) for name, entries in CATEGORIES.items()},
        "stats": library_stats(),
    }
