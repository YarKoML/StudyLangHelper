"""Роутер авторизации: регистрация, логин, /me."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from backend.deps import get_session
from backend.models import Dictionary, User
from backend.schemas import LoginRequest, Token, UserCreate, UserRead
from backend.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_read(u: User) -> UserRead:
    return UserRead(id=u.id, username=u.username, created_at=u.created_at)


@router.post("/register", response_model=Token, status_code=201)
def register(payload: UserCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.username == payload.username)).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already registered")

    user = User(username=payload.username, password_hash=hash_password(payload.password))
    session.add(user)
    session.commit()
    session.refresh(user)

    is_first = session.exec(select(User)).first().id == user.id
    if is_first:
        orphans = session.exec(select(Dictionary).where(Dictionary.user_id.is_(None))).all()
        for d in orphans:
            d.user_id = user.id
            session.add(d)
        session.commit()

    token = create_access_token(user.id)
    return Token(access_token=token, user=_to_read(user))


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == payload.username)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password")
    token = create_access_token(user.id)
    return Token(access_token=token, user=_to_read(user))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return _to_read(current_user)
