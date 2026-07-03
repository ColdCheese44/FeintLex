from __future__ import annotations

import logging
import re

from sqlmodel import Session

from feintlex.models import ContentItem


LOGGER = logging.getLogger("feintlex.content")
ALLOWED_SOURCE_TYPES = {"pasted_text", "article", "subtitle", "transcript", "manual_note"}

_TIMESTAMP_PATTERN = re.compile(r"\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->")
_MARKUP_PATTERN = re.compile(r"<[^>]+>|\{[^}]+\}")


def looks_like_subtitles(text: str) -> bool:
    return bool(_TIMESTAMP_PATTERN.search(text)) or text.lstrip().startswith("WEBVTT")


def clean_subtitles(text: str) -> str:
    """Strip SRT/VTT cruft: indices, timestamps, markup, duplicate lines."""
    bom = "﻿"
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip().lstrip(bom).strip()
        if not line:
            continue
        if line == "WEBVTT" or line.startswith(("NOTE ", "NOTE\t", "STYLE", "REGION")):
            continue
        if _TIMESTAMP_PATTERN.search(line):
            continue
        if line.isdigit():
            continue
        line = _MARKUP_PATTERN.sub("", line).strip()
        line = line.lstrip("-–— ").strip()
        if not line:
            continue
        if lines and lines[-1] == line:
            continue
        lines.append(line)
    return "\n".join(lines)


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
    if looks_like_subtitles(cleaned):
        cleaned = clean_subtitles(cleaned)
        source_type = "subtitle"
        if not cleaned:
            raise ValueError("Subtitle file contained no dialogue lines.")

    item = ContentItem(text=cleaned, source_type=source_type, topic_tags=topic_tags or [])
    session.add(item)
    session.commit()
    session.refresh(item)
    LOGGER.info("content_imported", extra={"content_id": item.id, "source_type": source_type})
    return item
