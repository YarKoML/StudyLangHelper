"""Роутер статистики и календаря активности."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, func, select

from backend.deps import get_session
from backend.models import Dictionary, StudySession, User, Word
from backend.schemas import CalendarDay, StatsRead
from backend.security import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsRead)
def get_stats(
    dictionary_id: int = Query(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    d = session.get(Dictionary, dictionary_id)
    if not d or d.user_id != current_user.id:
        raise HTTPException(404, "Dictionary not found")

    total_words = session.exec(
        select(func.count(Word.id)).where(Word.dictionary_id == dictionary_id)
    ).one()
    learned_words = session.exec(
        select(func.count(Word.id)).where(
            Word.dictionary_id == dictionary_id, Word.learned.is_(True)
        )
    ).one()
    learning_words = (total_words or 0) - (learned_words or 0)
    learned_pct = round((learned_words / total_words * 100), 1) if total_words else 0.0

    sessions = session.exec(
        select(StudySession).where(StudySession.dictionary_id == dictionary_id)
    ).all()
    active_days = {s.started_at.date() for s in sessions}
    streak = 0
    today = date.today()
    while today in active_days:
        streak += 1
        today -= timedelta(days=1)

    return StatsRead(
        total_words=total_words or 0,
        learned_words=learned_words or 0,
        learning_words=learning_words,
        learned_pct=learned_pct,
        streak_days=streak,
    )


@router.get("/calendar", response_model=list[CalendarDay])
def get_calendar(
    dictionary_id: int = Query(...),
    year: int = Query(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    d = session.get(Dictionary, dictionary_id)
    if not d or d.user_id != current_user.id:
        raise HTTPException(404, "Dictionary not found")

    sessions = session.exec(
        select(StudySession).where(StudySession.dictionary_id == dictionary_id)
    ).all()
    counts: dict[str, int] = {}
    for s in sessions:
        if s.started_at.year != year:
            continue
        key = s.started_at.date().isoformat()
        counts[key] = counts.get(key, 0) + 1
    return [CalendarDay(date=d, count=c) for d, c in sorted(counts.items())]
