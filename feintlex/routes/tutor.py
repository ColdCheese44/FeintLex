from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from feintlex.db import get_session
from feintlex.models import Lesson
from feintlex.services.tutor import TutorContext, generate_tutor_response
from feintlex.services.tutor_chat import (
    capture_term,
    clear_history,
    get_all_mastery,
    get_captured,
    get_history,
    respond_chat,
    sync_mastery,
)


router = APIRouter()


class TutorRequest(BaseModel):
    message: str = Field(default="")
    action: str | None = None
    lesson_id: int | None = None
    selected_term: str | None = None
    selected_deck: str | None = None


class TutorChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_key: str = Field(default="default", max_length=100)
    lesson_id: int | None = None


class MasterySyncRequest(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)


class CaptureRequest(BaseModel):
    term: str = Field(min_length=1, max_length=80)
    translation: str = Field(default="", max_length=200)
    context: str = Field(default="", max_length=400)


@router.post("/tutor/respond")
def tutor_response_route(payload: TutorRequest, session: Session = Depends(get_session)):
    lesson = None
    if payload.lesson_id is not None:
        lesson = session.get(Lesson, payload.lesson_id)
        if lesson is None:
            raise HTTPException(status_code=404, detail=f"Lesson {payload.lesson_id} was not found.")

    return generate_tutor_response(
        payload.message,
        action=payload.action,
        context=TutorContext(
            lesson=lesson,
            selected_term=payload.selected_term,
            selected_deck=payload.selected_deck,
        ),
    )


@router.post("/tutor/chat")
def tutor_chat_route(payload: TutorChatRequest, session: Session = Depends(get_session)):
    if payload.lesson_id is not None and session.get(Lesson, payload.lesson_id) is None:
        raise HTTPException(status_code=404, detail=f"Lesson {payload.lesson_id} was not found.")
    return respond_chat(
        session,
        payload.message,
        session_key=payload.session_key,
        lesson_id=payload.lesson_id,
    )


@router.get("/tutor/chat/history")
def tutor_history_route(
    session_key: str = Query(default="default", max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    return get_history(session, session_key=session_key, limit=limit)


@router.delete("/tutor/chat/history")
def tutor_clear_history_route(
    session_key: str = Query(default="default", max_length=100),
    session: Session = Depends(get_session),
):
    deleted = clear_history(session, session_key=session_key)
    return {"deleted": deleted, "session_key": session_key}


@router.get("/tutor/mastery")
def tutor_mastery_route(session: Session = Depends(get_session)):
    return get_all_mastery(session)


@router.put("/tutor/mastery")
def tutor_mastery_sync_route(payload: MasterySyncRequest, session: Session = Depends(get_session)):
    return sync_mastery(session, payload.items)


@router.post("/tutor/capture")
def tutor_capture_route(payload: CaptureRequest, session: Session = Depends(get_session)):
    try:
        return capture_term(
            session,
            term=payload.term,
            translation=payload.translation,
            context=payload.context,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tutor/captured")
def tutor_captured_route(session: Session = Depends(get_session)):
    return get_captured(session)
