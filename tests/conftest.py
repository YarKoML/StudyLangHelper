"""Конфигурация pytest: in-memory SQLite для всех тестов."""

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

import backend.models  # noqa: F401 — регистрация таблиц в metadata
from backend import database


@pytest.fixture(name="client", autouse=True)
def client_fixture():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)

    original_engine = database.engine
    database.engine = test_engine

    from fastapi.testclient import TestClient

    from backend.main import app

    with TestClient(app) as client:
        yield client

    database.engine = original_engine
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="authed_client")
def authed_client_fixture(client):
    """Залогиненный клиент с настроенным Bearer-заголовком."""
    client.post(
        "/auth/register",
        json={"username": "tester", "password": "testpass"},
    )
    r = client.post(
        "/auth/login",
        json={"username": "tester", "password": "testpass"},
    )
    token = r.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
