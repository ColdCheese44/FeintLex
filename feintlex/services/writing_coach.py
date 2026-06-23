from __future__ import annotations

import logging

from sqlmodel import Session

from feintlex.models import WritingSubmission


LOGGER = logging.getLogger("feintlex.writing")


def submit_writing(
    session: Session,
    submitted_text: str,
    *,
    related_lesson_id: int | None = None,
) -> WritingSubmission:
    cleaned = submitted_text.strip()
    if not cleaned:
        raise ValueError("Submitted text cannot be empty.")

    feedback = WritingSubmission(
        submitted_text=cleaned,
        corrected_version=cleaned,
        strengths=["Submission captured for review.", "MVP fallback keeps your original wording visible."],
        issues=["LLM correction is not enabled yet; run manual review against lesson patterns."],
        grammar_notes=["TODO: attach provider-backed correction while preserving offline fallback."],
        rewrite_prompt="Rewrite the text once using one connector and one clearly marked verb tense.",
        related_lesson_id=related_lesson_id,
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    LOGGER.info("writing_submitted", extra={"writing_submission_id": feedback.id})
    return feedback
