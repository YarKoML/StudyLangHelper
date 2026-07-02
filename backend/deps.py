"""FastAPI dependencies."""

from collections.abc import Generator

from sqlmodel import Session

from backend import database


def get_session() -> Generator[Session, None, None]:
    with Session(database.engine) as session:
        yield session