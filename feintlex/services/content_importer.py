from __future__ import annotations

import logging

from sqlmodel import Session

from feintlex.models import ContentItem


LOGGER = logging.getLogger("feintlex.content")
ALLOWED_SOURCE_TYPES = {"pasted_text", "article", "subtitle", "transcript", "manual_note"}


def import_content(
    session: Session,
    text: str,
    *,
    source_type: str = "pasted_text",
    topic_tags: list[str] | None = None,
) -> ContentItem:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Content text cannot be empty.")
    if source_type not in ALLOWED_SOURCE_TYPES:
        raise ValueError(f"Unsupported source_type: {source_type}")

    item = ContentItem(text=cleaned, source_type=source_type, topic_tags=topic_tags or [])
    session.add(item)
    session.commit()
    session.refresh(item)
    LOGGER.info("content_imported", extra={"content_id": item.id, "source_type": source_type})
    return item
