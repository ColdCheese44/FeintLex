from __future__ import annotations

"""HQ status: XP, tactical ranks, and activity streaks.

Turns raw training activity into command-center feedback. XP is computed
from the database on every request (no separate ledger to corrupt), ranks
follow a tactical ladder, and the streak counts consecutive local days
with any real training activity.
"""

import logging
from datetime import UTC, date, timedelta

from sqlmodel import Session, func, select

from feintlex.models import (
    Lesson,
    Mistake,
    SentenceAutopsy,
    TutorChatMessage,
    TutorMastery,
    WritingSubmission,
)
from feintlex.services.program import known_signal_count


LOGGER = logging.getLogger("feintlex.hq")

# (xp_threshold, rank name) — tactical ladder, cheap to extend.
RANKS: list[tuple[int, str]] = [
    (0, "Recruit"),
    (100, "Field Trainee"),
    (300, "Signal Analyst"),
    (700, "Cipher Operator"),
    (1500, "Field Agent"),
    (3000, "Signal Officer"),
    (6000, "Station Chief"),
    (12000, "Spymaster"),
]

XP_WEIGHTS = {
    "lesson": 25,
    "autopsy": 10,
    "writing": 15,
    "chat": 2,
    "known_signal": 10,
    "locked_signal": 15,
    "mistake_reviewed": 5,
}


def _count(session: Session, statement) -> int:
    return int(session.exec(statement).one())


def compute_xp(session: Session) -> dict[str, int]:
    lessons = _count(session, select(func.count()).select_from(Lesson))
    autopsies = _count(session, select(func.count()).select_from(SentenceAutopsy))
    writings = _count(session, select(func.count()).select_from(WritingSubmission))
    chats = _count(
        session,
        select(func.count()).select_from(TutorChatMessage).where(TutorChatMessage.role == "user"),
    )
    known = known_signal_count(session)
    locked = _count(
        session, select(func.count()).select_from(TutorMastery).where(TutorMastery.level >= 5)
    )
    reviewed = _count(
        session, select(func.count()).select_from(Mistake).where(Mistake.review_count >= 1)
    )

    breakdown = {
        "lessons": lessons * XP_WEIGHTS["lesson"],
        "autopsies": autopsies * XP_WEIGHTS["autopsy"],
        "writing": writings * XP_WEIGHTS["writing"],
        "chat": chats * XP_WEIGHTS["chat"],
        "known_signals": known * XP_WEIGHTS["known_signal"],
        "locked_signals": locked * XP_WEIGHTS["locked_signal"],
        "mistakes_reviewed": reviewed * XP_WEIGHTS["mistake_reviewed"],
    }
    breakdown["total"] = sum(breakdown.values())
    return breakdown


def rank_for_xp(xp: int) -> dict[str, object]:
    current_threshold, current_name = RANKS[0]
    next_threshold: int | None = None
    next_name: str | None = None
    for index, (threshold, name) in enumerate(RANKS):
        if xp >= threshold:
            current_threshold, current_name = threshold, name
            if index + 1 < len(RANKS):
                next_threshold, next_name = RANKS[index + 1]
            else:
                next_threshold, next_name = None, None
    if next_threshold is None:
        progress = 1.0
    else:
        span = next_threshold - current_threshold
        progress = (xp - current_threshold) / span if span else 1.0
    return {
        "rank": current_name,
        "rank_threshold": current_threshold,
        "next_rank": next_name,
        "next_rank_xp": next_threshold,
        "rank_progress": round(min(1.0, max(0.0, progress)), 3),
    }


def _local_date(timestamp) -> date:
    return timestamp.replace(tzinfo=UTC).astimezone().date()


def _activity_dates(session: Session) -> set[date]:
    dates: set[date] = set()
    for column in (
        Lesson.created_at,
        SentenceAutopsy.created_at,
        WritingSubmission.created_at,
    ):
        for timestamp in session.exec(select(column)).all():
            dates.add(_local_date(timestamp))
    for timestamp in session.exec(
        select(TutorChatMessage.created_at).where(TutorChatMessage.role == "user")
    ).all():
        dates.add(_local_date(timestamp))
    # Mastery rows only count when they carry real signal (see program.py).
    for timestamp in session.exec(
        select(TutorMastery.updated_at).where(
            (TutorMastery.level > 0) | (TutorMastery.seen > 0) | (TutorMastery.correct > 0)
        )
    ).all():
        dates.add(_local_date(timestamp))
    return dates


def activity_streak(session: Session) -> dict[str, object]:
    from datetime import datetime

    dates = _activity_dates(session)
    today = datetime.now().astimezone().date()
    active_today = today in dates

    # Grace: an unbroken run ending yesterday still counts until today ends.
    cursor = today if active_today else today - timedelta(days=1)
    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return {"streak_days": streak, "active_today": active_today}


def build_hq_status(session: Session) -> dict[str, object]:
    xp = compute_xp(session)
    rank = rank_for_xp(xp["total"])
    streak = activity_streak(session)
    status = {
        "xp": xp["total"],
        "xp_breakdown": xp,
        **rank,
        **streak,
    }
    LOGGER.info("hq_status", extra={"xp": xp["total"], "rank": rank["rank"], "streak": streak["streak_days"]})
    return status
