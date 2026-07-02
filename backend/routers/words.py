"""Роутер слов словаря."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from backend.deps import get_session
from backend.models import Dictionary, User, Word
from backend.schemas import WordBatchCreate, WordCreate, WordRead, WordUpdate
from backend.security import get_current_user

router = APIRouter(tags=["words"])


def _to_read(w: Word) -> WordRead:
    return WordRead(
        id=w.id,
        dictionary_id=w.dictionary_id,
        word=w.word,
        translation=w.translation,
        correct_count=w.correct_count,
        learned=w.learned,
        created_at=w.created_at,
    )


def _get_owned_dictionary(session: Session, dict_id: int, current_user: User) -> Dictionary:
    d = session.get(Dictionary, dict_id)
    if not d or d.user_id != current_user.id:
        raise HTTPException(404, "Dictionary not found")
    return d


@router.post("/dictionaries/{dict_id}/words", response_model=WordRead, status_code=201)
def create_word(
    dict_id: int,
    payload: WordCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    _get_owned_dictionary(session, dict_id, current_user)
    w = Word(dictionary_id=dict_id, word=payload.word, translation=payload.translation)
    session.add(w)
    session.commit()
    session.refresh(w)
    return _to_read(w)


@router.post("/dictionaries/{dict_id}/words/batch", response_model=list[WordRead], status_code=201)
def create_words_batch(
    dict_id: int,
    payload: WordBatchCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    _get_owned_dictionary(session, dict_id, current_user)
    created: list[Word] = []
    for item in payload.words:
        w = Word(dictionary_id=dict_id, word=item.word, translation=item.translation)
        session.add(w)
        created.append(w)
    session.commit()
    for w in created:
        session.refresh(w)
    return [_to_read(w) for w in created]


@router.get("/dictionaries/{dict_id}/words", response_model=list[WordRead])
def list_words(
    dict_id: int,
    session: Session = Depends(get_session),
    learned: str = Query("all", pattern="^(all|true|false)$"),
    current_user: User = Depends(get_current_user),
):
    _get_owned_dictionary(session, dict_id, current_user)
    stmt = select(Word).where(Word.dictionary_id == dict_id).order_by(Word.created_at)
    if learned == "true":
        stmt = stmt.where(Word.learned.is_(True))
    elif learned == "false":
        stmt = stmt.where(Word.learned.is_(False))
    words = session.exec(stmt).all()
    return [_to_read(w) for w in words]


@router.patch("/words/{word_id}", response_model=WordRead)
def update_word(
    word_id: int,
    payload: WordUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    w = session.get(Word, word_id)
    if not w:
        raise HTTPException(404, "Word not found")
    d = session.get(Dictionary, w.dictionary_id)
    if not d or d.user_id != current_user.id:
        raise HTTPException(404, "Word not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        if v is not None:
            setattr(w, k, v)
    session.add(w)
    session.commit()
    session.refresh(w)
    return _to_read(w)


@router.delete("/words/{word_id}", status_code=204)
def delete_word(
    word_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    w = session.get(Word, word_id)
    if not w:
        raise HTTPException(404, "Word not found")
    d = session.get(Dictionary, w.dictionary_id)
    if not d or d.user_id != current_user.id:
        raise HTTPException(404, "Word not found")
    session.delete(w)
    session.commit()
