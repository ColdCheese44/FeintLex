from __future__ import annotations

"""Unified review queue.

Blends every reinforcement source into one prioritized, gradeable queue:
1. due mistakes from the mistake bank (highest priority)
2. due review items (lesson vocabulary + sentence patterns)
3. weak tutor deck terms tracked in TutorMastery

Grading feeds back into each source: mistakes reschedule through SRS,
review items complete or retry, and mastery levels move up or down.
"""

import logging
from datetime import timedelta

from sqlmodel import Session, select

from feintlex.models import Mistake, ReviewItem, TutorMastery, utc_now
from feintlex.services.mistake_bank import get_due_mistakes, mark_mistake_reviewed
from feintlex.services.lexicon import lookup


LOGGER = logging.getLogger("feintlex.review_queue")

QUEUE_KINDS = {"mistake", "review_item", "term"}


def build_review_queue(session: Session, *, limit: int = 20) -> list[dict[str, object]]:
    queue: list[dict[str, object]] = []

    for mistake in get_due_mistakes(session):
        queue.append(
            {
                "kind": "mistake",
                "id": mistake.id,
                "badge": mistake.mistake_type,
                "prompt": f"Fix this: {mistake.original_input}",
                "answer": mistake.correction,
                "explanation": mistake.explanation,
                "speak": None,
                "priority": 0,
            }
        )

    review_items = session.exec(
        select(ReviewItem)
        .where(ReviewItem.due_at <= utc_now())
        .where(ReviewItem.status == "due")
        .order_by(ReviewItem.due_at)
    ).all()
    for item in review_items:
        queue.append(
            {
                "kind": "review_item",
                "id": item.id,
                "badge": item.item_type,
                "prompt": item.prompt,
                "answer": item.answer,
                "explanation": None,
                "speak": None,
                "priority": 1,
            }
        )

    weak_terms = session.exec(
        select(TutorMastery)
        .where(TutorMastery.level <= 2)
        .where(TutorMastery.term != "")
        .order_by(TutorMastery.level, TutorMastery.updated_at)
        .limit(limit)
    ).all()
    for term in weak_terms:
        translation = term.translation or lookup(term.term) or ""
        if not translation:
            continue
        queue.append(
            {
                "kind": "term",
                "id": term.id,
                "badge": f"signal L{term.level}",
                "prompt": f"Translate: {term.term}",
                "answer": translation,
                "explanation": f"Deck term ({term.deck_id or 'tutor'}). Say it aloud, then use it in a sentence.",
                "speak": term.term,
                "priority": 2,
            }
        )

    queue.sort(key=lambda entry: entry["priority"])
    return queue[:limit]


def complete_review(
    session: Session,
    *,
    kind: str,
    item_id: int,
    result: str,
) -> dict[str, object]:
    """Grade a queue item. result is 'got' or 'missed'."""
    if kind not in QUEUE_KINDS:
        raise ValueError(f"Unknown review kind '{kind}'.")
    if result not in {"got", "missed"}:
        raise ValueError(f"Unknown review result '{result}'.")

    if kind == "mistake":
        mistake = session.get(Mistake, item_id)
        if mistake is None:
            raise ValueError(f"Mistake {item_id} was not found.")
        if result == "got":
            mistake = mark_mistake_reviewed(session, item_id)
            status = mistake.status
        else:
            mistake.review_count = 0
            mistake.status = "new"
            mistake.review_due_at = utc_now() + timedelta(days=1)
            mistake.updated_at = utc_now()
            session.add(mistake)
            session.commit()
            status = mistake.status
        return {"kind": kind, "id": item_id, "result": result, "status": status}

    if kind == "review_item":
        item = session.get(ReviewItem, item_id)
        if item is None:
            raise ValueError(f"Review item {item_id} was not found.")
        if result == "got":
            item.status = "done"
        else:
            item.due_at = utc_now() + timedelta(days=1)
        session.add(item)
        session.commit()
        return {"kind": kind, "id": item_id, "result": result, "status": item.status}

    term = session.get(TutorMastery, item_id)
    if term is None:
        raise ValueError(f"Mastery term {item_id} was not found.")
    delta = 1 if result == "got" else -1
    term.level = max(0, min(5, term.level + delta))
    term.seen += 1
    if result == "got":
        term.correct += 1
    term.updated_at = utc_now()
    session.add(term)
    session.commit()
    LOGGER.info("review_completed", extra={"kind": kind, "item_id": item_id, "result": result})
    return {"kind": kind, "id": item_id, "result": result, "level": term.level}
