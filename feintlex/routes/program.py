from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from feintlex.db import get_session
from feintlex.services.program import build_daily_mission


router = APIRouter()


@router.get("/program/today")
def program_today_route(session: Session = Depends(get_session)):
    return build_daily_mission(session)
