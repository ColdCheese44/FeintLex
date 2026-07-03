from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from feintlex.db import get_session
from feintlex.services.methods import build_constructor_session, build_echo_session, record_method_results


router = APIRouter()


class MethodResultsRequest(BaseModel):
    method: str = Field(pattern="^(echo|constructor)$")
    results: list[dict[str, Any]] = Field(default_factory=list)


@router.get("/methods/session")
def method_session_route(
    method: str = Query(pattern="^(echo|constructor)$"),
    size: int = Query(default=6, ge=3, le=10),
    session: Session = Depends(get_session),
):
    if method == "echo":
        return build_echo_session(session, size=size)
    return build_constructor_session(session)


@router.post("/methods/complete")
def method_complete_route(payload: MethodResultsRequest, session: Session = Depends(get_session)):
    if not payload.results:
        raise HTTPException(status_code=400, detail="No results to record.")
    return record_method_results(session, method=payload.method, results=payload.results)
