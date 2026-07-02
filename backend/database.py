"""Параметры подключения к БД и инициализация таблиц."""

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from backend.config import DATABASE_URL

connect_args = {"check_same_thread": False}

_db_file = DATABASE_URL.replace("sqlite:///", "", 1)
if _db_file:
    Path(_db_file).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session