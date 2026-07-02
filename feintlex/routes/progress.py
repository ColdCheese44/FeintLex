from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, func, select

from feintlex.db import get_session
from feintlex.models import (
    Lesson,
    Mistake,
    ReviewItem,
    TutorChatMessage,
    TutorMastery,
    VocabularyEntry,
    WritingSubmission,
    utc_now,
)
from feintlex.services.mistake_bank import get_due_mistakes
from feintlex.services.review_queue import build_review_queue, complete_review


router = APIRouter()


class ReviewCompleteRequest(BaseModel):
    kind: str = Field(min_length=1)
    id: int
    result: str = Field(pattern="^(got|missed)$")


@router.get("/review/due")
def review_due_route(session: Session = Depends(get_session)):
    review_items = session.exec(
        select(ReviewItem).where(ReviewItem.due_at <= utc_now()).where(ReviewItem.status == "due")
    ).all()
    return {
        "mistakes": list(get_due_mistakes(session)),
        "review_items": list(review_items),
    }


@router.get("/review/queue")
def review_queue_route(limit: int = 20, session: Session = Depends(get_session)):
    return build_review_queue(session, limit=max(1, min(limit, 50)))


@router.post("/review/complete")
def review_complete_route(payload: ReviewCompleteRequest, session: Session = Depends(get_session)):
    try:
        return complete_review(session, kind=payload.kind, item_id=payload.id, result=payload.result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _count(session: Session, statement) -> int:
    return session.exec(statement).one()


@router.get("/progress/summary")
def progress_summary_route(session: Session = Depends(get_session)):
    now = utc_now()
    return {
        "lessons": _count(session, select(func.count()).select_from(Lesson)),
        "vocabulary_terms": _count(session, select(func.count()).select_from(VocabularyEntry)),
        "writing_submissions": _count(session, select(func.count()).select_from(WritingSubmission)),
        "chat_messages": _count(session, select(func.count()).select_from(TutorChatMessage)),
        "mistakes_total": _count(session, select(func.count()).select_from(Mistake)),
        "mistakes_due": _count(
            session,
            select(func.count()).select_from(Mistake).where(Mistake.review_due_at <= now).where(Mistake.status != "mastered"),
        ),
        "review_items_due": _count(
            session,
            select(func.count()).select_from(ReviewItem).where(ReviewItem.due_at <= now).where(ReviewItem.status == "due"),
        ),
        "mastery_tracked": _count(
            session, select(func.count()).select_from(TutorMastery).where(TutorMastery.level > 0)
        ),
        "mastery_locked": _count(
            session, select(func.count()).select_from(TutorMastery).where(TutorMastery.level >= 5)
        ),
    }
