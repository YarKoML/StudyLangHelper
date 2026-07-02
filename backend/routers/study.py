"""Роутер учебных сессий (карточек)."""

import random
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from backend.deps import get_session
from backend.models import (
    Answer,
    Dictionary,
    StudyDirection,
    StudyMode,
    StudySession,
    Word,
)
from backend.schemas import (
    AnswerCreate,
    AnswerResult,
    Question,
    SessionResult,
    StudySessionCreate,
    StudySessionRead,
)

router = APIRouter(prefix="/study", tags=["study"])

MIN_WORDS_FOR_OPTIONS = 4


def _pick_prompt_translation(w: Word, direction: StudyDirection) -> tuple[str, str]:
    if direction == StudyDirection.word_to_translation:
        return w.word, w.translation
    return w.translation, w.word


def _build_question(
    target: Word,
    pool: list[Word],
    direction: StudyDirection,
) -> Question:
    prompt, correct_answer = _pick_prompt_translation(target, direction)

    distractors = [w for w in pool if w.id != target.id]
    random.shuffle(distractors)
    distractor_answers = []
    for w in distractors[:3]:
        _, ans = _pick_prompt_translation(w, direction)
        distractor_answers.append(ans)

    options = distractor_answers + [correct_answer]
    random.shuffle(options)
    correct_index = options.index(correct_answer)
    return Question(word_id=target.id, prompt=prompt, options=options, correct_index=correct_index)


@router.post("/sessions", response_model=StudySessionRead)
def start_session(payload: StudySessionCreate, session: Session = Depends(get_session)):
    d = session.get(Dictionary, payload.dictionary_id)
    if not d:
        raise HTTPException(404, "Dictionary not found")

    all_words = list(
        session.exec(select(Word).where(Word.dictionary_id == d.id)).all()
    )
    if len(all_words) < MIN_WORDS_FOR_OPTIONS:
        raise HTTPException(
            400,
            f"Dictionary must have at least {MIN_WORDS_FOR_OPTIONS} words to generate options",
        )

    if payload.mode == StudyMode.review:
        candidates = [w for w in all_words if w.learned]
        if not candidates:
            raise HTTPException(400, "No learned words to review yet")
    else:
        candidates = [w for w in all_words if not w.learned]
        if not candidates:
            raise HTTPException(400, "No new words available")

    count = min(payload.count, len(candidates))
    selected = random.sample(candidates, count)

    ss = StudySession(
        dictionary_id=d.id,
        mode=payload.mode,
        direction=payload.direction,
        total=count,
        correct=0,
    )
    session.add(ss)
    session.commit()
    session.refresh(ss)

    questions = [_build_question(w, all_words, payload.direction) for w in selected]
    return StudySessionRead(session_id=ss.id, questions=questions)


@router.post("/sessions/{session_id}/answer", response_model=AnswerResult)
def submit_answer(session_id: int, payload: AnswerCreate, session: Session = Depends(get_session)):
    ss = session.get(StudySession, session_id)
    if not ss:
        raise HTTPException(404, "Session not found")
    if ss.finished_at is not None:
        raise HTTPException(400, "Session already finished")

    w = session.get(Word, payload.word_id)
    if not w:
        raise HTTPException(404, "Word not found")

    _, correct_answer = _pick_prompt_translation(w, ss.direction)
    is_correct = payload.chosen == correct_answer

    session.add(
        Answer(
            session_id=ss.id,
            word_id=w.id,
            chosen=payload.chosen,
            is_correct=is_correct,
        )
    )
    if is_correct:
        ss.correct += 1
        w.correct_count += 1
        d = session.get(Dictionary, ss.dictionary_id)
        if d:
            w.learned = w.correct_count >= d.n_to_learn
        session.add(w)
    session.add(ss)
    session.commit()

    return AnswerResult(is_correct=is_correct, correct_translation=correct_answer)


@router.post("/sessions/{session_id}/finish", response_model=SessionResult)
def finish_session(session_id: int, session: Session = Depends(get_session)):
    ss = session.get(StudySession, session_id)
    if not ss:
        raise HTTPException(404, "Session not found")
    if ss.finished_at is None:
        ss.finished_at = datetime.now(UTC)
        session.add(ss)
        session.commit()
        session.refresh(ss)

    wrong = ss.total - ss.correct
    correct_pct = (ss.correct / ss.total * 100) if ss.total else 0.0
    wrong_pct = (wrong / ss.total * 100) if ss.total else 0.0
    return SessionResult(
        total=ss.total,
        correct=ss.correct,
        wrong=wrong,
        correct_pct=round(correct_pct, 1),
        wrong_pct=round(wrong_pct, 1),
    )