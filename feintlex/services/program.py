from __future__ import annotations

"""The FeintLex Protocol: daily mission engine.

Implements the research-backed training program in PROGRAM.md as live,
self-tracking daily missions. Mission completion is inferred from today's
database activity — no manual checkboxes to maintain.

Strand weighting follows Nation's Four Strands adapted for a
reading/writing-first learner: 40% input / 25% output / 25% deliberate
study / 10% fluency.
"""

import logging
from datetime import UTC, datetime

from sqlmodel import Session, func, select

from feintlex.models import (
    ContentItem,
    SentenceAutopsy,
    TutorChatMessage,
    TutorMastery,
    VocabularyEntry,
    WritingSubmission,
)
from feintlex.services.review_queue import build_review_queue


LOGGER = logging.getLogger("feintlex.program")

# Phase thresholds in "known signals" (see PROGRAM.md milestones).
PHASES = [
    {"phase": 1, "name": "Foundation", "threshold": 0, "focus": "Lock the core decks and present-tense writing."},
    {"phase": 2, "name": "Signal Expansion", "threshold": 300, "focus": "Graded readers at 98% coverage; past-tense retellings."},
    {"phase": 3, "name": "Field Immersion", "threshold": 1000, "focus": "Real news and subtitles; aggressive 1T sentence mining."},
    {"phase": 4, "name": "Native Operations", "threshold": 3000, "focus": "Long-form reading volume; maintenance reviews."},
]


def _today_start():
    """Local midnight expressed as naive UTC, matching stored timestamps.

    FeintLex is local-first: a mission done at 9pm local should count for
    the local day even when that is already 'tomorrow' in UTC.
    """
    local_midnight = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    return local_midnight.astimezone(UTC).replace(tzinfo=None)


def known_signal_count(session: Session) -> int:
    """Proxy for 'known words': mastered deck terms + repeatedly-seen vocabulary.

    Research basis: a word needs roughly 8+ contextual encounters to stick
    (Brown et al. 2008), so vocabulary entries seen 3+ times across lessons
    count as 'known-ish'; deck terms count once they reach signal level 3.
    """
    mastered = session.exec(
        select(func.count()).select_from(TutorMastery).where(TutorMastery.level >= 3)
    ).one()
    seen_vocab = session.exec(
        select(func.count()).select_from(VocabularyEntry).where(VocabularyEntry.frequency >= 3)
    ).one()
    return int(mastered) + int(seen_vocab)


def current_phase(known: int) -> dict[str, object]:
    active = PHASES[0]
    for phase in PHASES:
        if known >= int(phase["threshold"]):
            active = phase
    next_index = PHASES.index(active) + 1
    next_threshold = int(PHASES[next_index]["threshold"]) if next_index < len(PHASES) else None
    return {
        "phase": active["phase"],
        "name": active["name"],
        "focus": active["focus"],
        "known_signals": known,
        "next_threshold": next_threshold,
    }


def _count_today(session: Session, model, column) -> int:
    return int(
        session.exec(select(func.count()).select_from(model).where(column >= _today_start())).one()
    )


def build_daily_mission(session: Session) -> dict[str, object]:
    known = known_signal_count(session)
    phase = current_phase(known)

    queue_size = len(build_review_queue(session, limit=50))
    imports_today = _count_today(session, ContentItem, ContentItem.created_at)
    autopsies_today = _count_today(session, SentenceAutopsy, SentenceAutopsy.created_at)
    writings_today = _count_today(session, WritingSubmission, WritingSubmission.created_at)
    # Rows created by the dashboard's snapshot push start at zero; only rows
    # carrying real signal (a level, a seen count) reflect drill activity.
    drills_today = int(
        session.exec(
            select(func.count())
            .select_from(TutorMastery)
            .where(TutorMastery.updated_at >= _today_start())
            .where((TutorMastery.level > 0) | (TutorMastery.seen > 0) | (TutorMastery.correct > 0))
        ).one()
    )
    quiz_chats_today = int(
        session.exec(
            select(func.count())
            .select_from(TutorChatMessage)
            .where(TutorChatMessage.created_at >= _today_start())
            .where(TutorChatMessage.intent == "quiz")
        ).one()
    )

    missions = [
        {
            "id": "queue",
            "title": "Clear the Signal Queue",
            "detail": f"{queue_size} item(s) due. Answer from memory, then grade honestly.",
            "strand": "study",
            "minutes": 10,
            "done": queue_size == 0,
            "manual": False,
        },
        {
            "id": "read",
            "title": "Import + read one Spanish text",
            "detail": "150+ words at 95%+ comprehension. News, match report, or subtitles.",
            "strand": "input",
            "minutes": 20,
            "done": imports_today >= 1,
            "manual": False,
        },
        {
            "id": "autopsy",
            "title": "Autopsy 2 sentences",
            "detail": f"{autopsies_today}/2 today. Isolate the verbs, connectors, and reusable pattern.",
            "strand": "study",
            "minutes": 10,
            "done": autopsies_today >= 2,
            "manual": False,
        },
        {
            "id": "write",
            "title": "Write 5+ sentences and submit",
            "detail": "React to today's text (summary, opinion, questions...). Read every correction.",
            "strand": "output",
            "minutes": 15,
            "done": writings_today >= 1,
            "manual": False,
        },
        {
            "id": "drill",
            "title": "Drill weak signals",
            "detail": "Flashcards, the Drill tab, or ask the coach to quiz you.",
            "strand": "study",
            "minutes": 5,
            "done": drills_today >= 1 or quiz_chats_today >= 1,
            "manual": False,
        },
        {
            "id": "listen",
            "title": "One listening pass (optional)",
            "detail": "Keep the ear alive: a few transmissions on the Listen tab.",
            "strand": "fluency",
            "minutes": 5,
            "done": False,
            "manual": True,
        },
    ]

    completed = sum(1 for mission in missions if mission["done"])
    LOGGER.info("daily_mission_built", extra={"completed": completed, "phase": phase["phase"]})
    return {
        **phase,
        "missions": missions,
        "completed": completed,
        "total": len(missions),
        "protocol_minutes": sum(int(mission["minutes"]) for mission in missions),
    }
