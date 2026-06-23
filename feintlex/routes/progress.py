from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from feintlex.db import get_session
from feintlex.models import ReviewItem, utc_now
from feintlex.services.mistake_bank import get_due_mistakes


router = APIRouter()


@router.get("/review/due")
def review_due_route(session: Session = Depends(get_session)):
    review_items = session.exec(
        select(ReviewItem).where(ReviewItem.due_at <= utc_now()).where(ReviewItem.status == "due")
    ).all()
    return {
        "mistakes": list(get_due_mistakes(session)),
        "review_items": list(review_items),
    }
