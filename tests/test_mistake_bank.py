from __future__ import annotations

from feintlex.models import utc_now
from feintlex.services.mistake_bank import create_mistake, get_due_mistakes, mark_mistake_reviewed


def test_mistake_bank_starts_due_and_schedules_after_review(isolated_session):
    mistake = create_mistake(
        isolated_session,
        mistake_type="verb_tense",
        original_input="Yo fue al estadio.",
        correction="Yo fui al estadio.",
        explanation="'Fui' is the first-person preterite form of ir/ser.",
    )

    assert mistake in get_due_mistakes(isolated_session)
    reviewed = mark_mistake_reviewed(isolated_session, mistake.id)
    assert reviewed.review_count == 1
    assert reviewed.review_due_at > utc_now()
    assert reviewed.status == "learning"
