from __future__ import annotations

from sqlmodel import Session, select

from feintlex.models import Mistake, utc_now
from feintlex.services.srs import next_review_due


def create_mistake(
    session: Session,
    *,
    mistake_type: str,
    original_input: str,
    correction: str,
    explanation: str,
    related_lesson_id: int | None = None,
) -> Mistake:
    mistake = Mistake(
        mistake_type=mistake_type,
        original_input=original_input,
        correction=correction,
        explanation=explanation,
        related_lesson_id=related_lesson_id,
    )
    session.add(mistake)
    session.commit()
    session.refresh(mistake)
    return mistake


def mark_mistake_reviewed(session: Session, mistake_id: int) -> Mistake:
    mistake = session.get(Mistake, mistake_id)
    if mistake is None:
        raise ValueError(f"Mistake {mistake_id} was not found.")
    mistake.review_count += 1
    mistake.status = "learning" if mistake.review_count < 3 else "familiar"
    mistake.review_due_at = next_review_due(mistake.review_count)
    mistake.updated_at = utc_now()
    session.add(mistake)
    session.commit()
    session.refresh(mistake)
    return mistake


def get_due_mistakes(session: Session) -> list[Mistake]:
    statement = (
        select(Mistake)
        .where(Mistake.review_due_at <= utc_now())
        .where(Mistake.status != "mastered")
        .order_by(Mistake.review_due_at)
    )
    return list(session.exec(statement).all())
