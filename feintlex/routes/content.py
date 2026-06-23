from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from feintlex.db import get_session
from feintlex.models import ContentItem
from feintlex.services.content_importer import import_content


router = APIRouter()


class ContentImportRequest(BaseModel):
    text: str = Field(min_length=1)
    source_type: str = "pasted_text"
    topic_tags: list[str] = Field(default_factory=list)


@router.post("/content/import")
def import_content_route(payload: ContentImportRequest, session: Session = Depends(get_session)):
    try:
        item = import_content(
            session,
            payload.text,
            source_type=payload.source_type,
            topic_tags=payload.topic_tags,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return item


@router.get("/content")
def list_content_route(limit: int = 20, session: Session = Depends(get_session)):
    limit = max(1, min(limit, 100))
    statement = select(ContentItem).order_by(ContentItem.created_at.desc()).limit(limit)
    return list(session.exec(statement).all())
