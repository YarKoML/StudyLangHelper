"""Конфигурация backend StudyLangHelper."""

import os
from pathlib import Path

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{Path(__file__).resolve().parent.parent / 'data' / 'studylanghelper.db'}",
)
_cors = os.environ.get("CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501")
CORS_ORIGINS = [o.strip() for o in _cors.split(",") if o.strip()]