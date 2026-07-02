"""Конфигурация backend StudyLangHelper."""

from pathlib import Path

DATABASE_URL = f"sqlite:///{Path(__file__).resolve().parent.parent / 'studylanghelper.db'}"
CORS_ORIGINS = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]