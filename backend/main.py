"""FastAPI приложение StudyLangHelper."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import CORS_ORIGINS
from backend.database import create_db_and_tables
from backend.routers import dictionaries, stats, study, words


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="StudyLangHelper API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dictionaries.router)
app.include_router(words.router)
app.include_router(study.router)
app.include_router(stats.router)


@app.get("/")
def root():
    return {"name": "StudyLangHelper API", "status": "ok"}