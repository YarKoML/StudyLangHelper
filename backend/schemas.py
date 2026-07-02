"""Pydantic/SQLModel схемы (create/read/update)."""

from datetime import datetime

from pydantic import BaseModel, field_validator

from backend.models import StudyDirection, StudyMode


class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("username must not be empty")
        return v

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("password must not be empty")
        return v


class UserRead(BaseModel):
    id: int
    username: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class LoginRequest(BaseModel):
    username: str
    password: str


class DictionaryCreate(BaseModel):
    native_lang: str
    study_lang: str
    n_to_learn: int = 5

    @field_validator("native_lang", "study_lang")
    @classmethod
    def lowercase_codes(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("study_lang")
    @classmethod
    def different_langs(cls, v: str, info) -> str:
        native = info.data.get("native_lang")
        if native and v == native:
            raise ValueError("study_lang must differ from native_lang")
        return v


class DictionaryRead(BaseModel):
    id: int
    native_lang: str
    study_lang: str
    n_to_learn: int
    created_at: datetime
    name: str | None = None


class DictionaryUpdate(BaseModel):
    n_to_learn: int | None = None


class WordCreate(BaseModel):
    word: str
    translation: str

    @field_validator("word", "translation")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be empty")
        return v


class WordRead(BaseModel):
    id: int
    dictionary_id: int
    word: str
    translation: str
    correct_count: int
    learned: bool
    created_at: datetime


class WordUpdate(BaseModel):
    word: str | None = None
    translation: str | None = None


class WordBatchCreate(BaseModel):
    words: list[WordCreate]

    @field_validator("words")
    @classmethod
    def at_least_one(cls, v: list[WordCreate]) -> list[WordCreate]:
        if not v:
            raise ValueError("words list must not be empty")
        return v


class StudySessionCreate(BaseModel):
    dictionary_id: int
    mode: StudyMode
    direction: StudyDirection
    count: int = 10

    @field_validator("count")
    @classmethod
    def positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("count must be >= 1")
        return v


class Question(BaseModel):
    word_id: int
    prompt: str
    options: list[str]
    correct_index: int


class StudySessionRead(BaseModel):
    session_id: int
    questions: list[Question]


class AnswerCreate(BaseModel):
    word_id: int
    chosen: str


class AnswerResult(BaseModel):
    is_correct: bool
    correct_translation: str


class SessionResult(BaseModel):
    total: int
    correct: int
    wrong: int
    correct_pct: float
    wrong_pct: float


class StatsRead(BaseModel):
    total_words: int
    learned_words: int
    learning_words: int
    learned_pct: float
    streak_days: int


class CalendarDay(BaseModel):
    date: str
    count: int


class LLMSettingsUpdate(BaseModel):
    base_url: str
    api_key: str
    model: str

    @field_validator("base_url", "api_key", "model")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be empty")
        return v


class LLMSettingsRead(BaseModel):
    base_url: str
    model: str
    has_key: bool


class LLMModelsRequest(BaseModel):
    base_url: str
    api_key: str


class LLMTranslateRequest(BaseModel):
    text: str
    dictionary_id: int

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("text must not be empty")
        return v


class LLMTranslateResult(BaseModel):
    translation: str


class LLMModelsList(BaseModel):
    models: list[str]


class BookRead(BaseModel):
    id: int
    title: str
    source_filename: str
    total_pages: int
    last_page: int
    created_at: datetime


class BookPageRead(BaseModel):
    id: int
    title: str
    total_pages: int
    current_page: int
    page_text: str


class BookUpdatePosition(BaseModel):
    last_page: int

    @field_validator("last_page")
    @classmethod
    def non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("last_page must be >= 0")
        return v
