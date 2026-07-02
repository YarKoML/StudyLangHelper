"""Роутер словарей (dictionaries)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from backend.deps import get_session
from backend.languages import dictionary_name, supported_languages
from backend.models import Dictionary, User, Word
from backend.schemas import DictionaryCreate, DictionaryRead, DictionaryUpdate
from backend.security import get_current_user
from backend.seed import seed_words

router = APIRouter(prefix="/dictionaries", tags=["dictionaries"])


def _to_read(d: Dictionary, ui_locale: str = "ru") -> DictionaryRead:
    return DictionaryRead(
        id=d.id,
        native_lang=d.native_lang,
        study_lang=d.study_lang,
        n_to_learn=d.n_to_learn,
        created_at=d.created_at,
        name=dictionary_name(d.native_lang, d.study_lang, ui_locale),
    )


@router.post("", response_model=DictionaryRead, status_code=201)
def create_dictionary(
    payload: DictionaryCreate,
    session: Session = Depends(get_session),
    ui_locale: str = Query("ru"),
    current_user: User = Depends(get_current_user),
):
    existing = session.exec(
        select(Dictionary).where(
            Dictionary.user_id == current_user.id,
            Dictionary.native_lang == payload.native_lang,
            Dictionary.study_lang == payload.study_lang,
        )
    ).first()
    if existing:
        raise HTTPException(409, "Dictionary for this language pair already exists")

    d = Dictionary(
        user_id=current_user.id,
        native_lang=payload.native_lang,
        study_lang=payload.study_lang,
        n_to_learn=payload.n_to_learn,
    )
    session.add(d)
    session.commit()
    session.refresh(d)

    for word, translation in seed_words(payload.native_lang, payload.study_lang):
        session.add(Word(dictionary_id=d.id, word=word, translation=translation))
    session.commit()

    return _to_read(d, ui_locale)


@router.get("", response_model=list[DictionaryRead])
def list_dictionaries(
    session: Session = Depends(get_session),
    ui_locale: str = Query("ru"),
    current_user: User = Depends(get_current_user),
):
    dicts = session.exec(
        select(Dictionary)
        .where(Dictionary.user_id == current_user.id)
        .order_by(Dictionary.created_at)
    ).all()
    return [_to_read(d, ui_locale) for d in dicts]


@router.get("/{dict_id}", response_model=DictionaryRead)
def get_dictionary(
    dict_id: int,
    session: Session = Depends(get_session),
    ui_locale: str = Query("ru"),
    current_user: User = Depends(get_current_user),
):
    d = session.get(Dictionary, dict_id)
    if not d or d.user_id != current_user.id:
        raise HTTPException(404, "Dictionary not found")
    return _to_read(d, ui_locale)


@router.patch("/{dict_id}", response_model=DictionaryRead)
def update_dictionary(
    dict_id: int,
    payload: DictionaryUpdate,
    session: Session = Depends(get_session),
    ui_locale: str = Query("ru"),
    current_user: User = Depends(get_current_user),
):
    d = session.get(Dictionary, dict_id)
    if not d or d.user_id != current_user.id:
        raise HTTPException(404, "Dictionary not found")

    if payload.n_to_learn is not None:
        d.n_to_learn = payload.n_to_learn
        session.add(d)
        session.commit()
        session.refresh(d)

        words = session.exec(select(Word).where(Word.dictionary_id == dict_id)).all()
        for w in words:
            w.learned = w.correct_count >= d.n_to_learn
            session.add(w)
        session.commit()

    return _to_read(d, ui_locale)


@router.delete("/{dict_id}", status_code=204)
def delete_dictionary(
    dict_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    d = session.get(Dictionary, dict_id)
    if not d or d.user_id != current_user.id:
        raise HTTPException(404, "Dictionary not found")
    session.delete(d)
    session.commit()


@router.get("/languages/list")
def list_languages(ui_locale: str = Query("ru")):
    return supported_languages(ui_locale)
