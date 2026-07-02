"""SQLModel-таблицы StudyLangHelper."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlmodel import Field, Relationship, SQLModel


class StudyMode(StrEnum):
    review = "review"
    new = "new"


class StudyDirection(StrEnum):
    word_to_translation = "word_to_translation"
    translation_to_word = "translation_to_word"


def _now() -> datetime:
    return datetime.now(UTC)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    created_at: datetime = Field(default_factory=_now)

    dictionaries: list["Dictionary"] = Relationship(back_populates="user")
    llm_settings: "LLMSettings" = Relationship(back_populates="user")
    books: list["Book"] = Relationship(back_populates="user", cascade_delete=True)


class Dictionary(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    native_lang: str = Field(index=True)
    study_lang: str = Field(index=True)
    n_to_learn: int = Field(default=5, ge=1)
    created_at: datetime = Field(default_factory=_now)

    user: User | None = Relationship(back_populates="dictionaries")
    words: list["Word"] = Relationship(back_populates="dictionary", cascade_delete=True)
    sessions: list["StudySession"] = Relationship(back_populates="dictionary", cascade_delete=True)


class Word(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    dictionary_id: int = Field(foreign_key="dictionary.id", ondelete="CASCADE", index=True)
    word: str
    translation: str
    correct_count: int = Field(default=0, ge=0)
    learned: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_now)

    dictionary: Dictionary | None = Relationship(back_populates="words")


class StudySession(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    dictionary_id: int = Field(foreign_key="dictionary.id", ondelete="CASCADE", index=True)
    mode: StudyMode
    direction: StudyDirection
    total: int = Field(default=0)
    correct: int = Field(default=0)
    started_at: datetime = Field(default_factory=_now)
    finished_at: datetime | None = Field(default=None)

    dictionary: Dictionary | None = Relationship(back_populates="sessions")
    answers: list["Answer"] = Relationship(back_populates="session", cascade_delete=True)


class Answer(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="studysession.id", ondelete="CASCADE", index=True)
    word_id: int = Field(foreign_key="word.id", ondelete="CASCADE")
    chosen: str
    is_correct: bool
    answered_at: datetime = Field(default_factory=_now)

    session: StudySession | None = Relationship(back_populates="answers")


class LLMSettings(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    base_url: str
    api_key: str
    model: str
    updated_at: datetime = Field(default_factory=_now)

    user: User | None = Relationship(back_populates="llm_settings")


class Book(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    title: str
    source_filename: str
    total_pages: int
    content: str
    last_page: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=_now)

    user: User | None = Relationship(back_populates="books")
