"""Тесты API StudyLangHelper.

БД in-memory + StaticPool настраивается в tests/conftest.py (autouse fixture).
Движок подменяется в backend.database.engine перед созданием TestClient.
"""

import pytest
from fastapi.testclient import TestClient

from backend.models import StudyDirection, StudyMode


@pytest.fixture(name="client")
def client_fixture(client: TestClient) -> TestClient:
    return client


# --- Auth ---


def test_register_login_me(client: TestClient):
    r = client.post("/auth/register", json={"username": "alice", "password": "pw1"})
    assert r.status_code == 201
    data = r.json()
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "alice"

    r = client.post("/auth/login", json={"username": "alice", "password": "pw1"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "alice"


def test_duplicate_user_409(client: TestClient):
    client.post("/auth/register", json={"username": "bob", "password": "pw"})
    r = client.post("/auth/register", json={"username": "bob", "password": "pw"})
    assert r.status_code == 409


def test_login_wrong_password_401(client: TestClient):
    client.post("/auth/register", json={"username": "bob", "password": "pw"})
    r = client.post("/auth/login", json={"username": "bob", "password": "wrong"})
    assert r.status_code == 401


def test_unauthorized_401(client: TestClient):
    r = client.get("/dictionaries")
    assert r.status_code == 401


def test_first_user_inherits_orphan_dicts(client: TestClient):
    from sqlmodel import Session

    from backend import database
    from backend.models import Dictionary

    with Session(database.engine) as s:
        s.add(Dictionary(native_lang="ru", study_lang="en", n_to_learn=5, user_id=None))
        s.commit()

    client.post("/auth/register", json={"username": "first", "password": "pw"})
    r = client.post("/auth/login", json={"username": "first", "password": "pw"})
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    dicts = client.get("/dictionaries", headers=h).json()
    assert len(dicts) == 1
    assert dicts[0]["native_lang"] == "ru"


def test_two_users_isolated(client: TestClient):
    client.post("/auth/register", json={"username": "u1", "password": "pw"})
    r1 = client.post("/auth/login", json={"username": "u1", "password": "pw"})
    h1 = {"Authorization": f"Bearer {r1.json()['access_token']}"}

    client.post("/auth/register", json={"username": "u2", "password": "pw"})
    r2 = client.post("/auth/login", json={"username": "u2", "password": "pw"})
    h2 = {"Authorization": f"Bearer {r2.json()['access_token']}"}

    client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 5},
        headers=h1,
    )

    dicts1 = client.get("/dictionaries", headers=h1).json()
    dicts2 = client.get("/dictionaries", headers=h2).json()
    assert len(dicts1) == 1
    assert len(dicts2) == 0


def test_access_other_user_dict_404(client: TestClient):
    client.post("/auth/register", json={"username": "u1", "password": "pw"})
    r1 = client.post("/auth/login", json={"username": "u1", "password": "pw"})
    h1 = {"Authorization": f"Bearer {r1.json()['access_token']}"}

    client.post("/auth/register", json={"username": "u2", "password": "pw"})
    r2 = client.post("/auth/login", json={"username": "u2", "password": "pw"})
    h2 = {"Authorization": f"Bearer {r2.json()['access_token']}"}

    d = client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 5},
        headers=h1,
    ).json()

    r = client.get(f"/dictionaries/{d['id']}", headers=h2)
    assert r.status_code == 404


# --- Dictionaries (authed) ---


def test_create_dictionary_ru_en_seeds_10_words(authed_client: TestClient):
    r = authed_client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 3},
    )
    assert r.status_code == 201
    d = r.json()
    assert d["native_lang"] == "ru"
    assert d["study_lang"] == "en"
    assert d["name"] == "Русский → Английский"

    words = authed_client.get(f"/dictionaries/{d['id']}/words").json()
    assert len(words) == 10
    assert all(w["correct_count"] == 0 for w in words)
    assert all(not w["learned"] for w in words)
    assert words[0]["word"] == "hello"
    assert words[0]["translation"] == "привет"


def test_create_dictionary_en_ru_seeds_reversed(authed_client: TestClient):
    r = authed_client.post(
        "/dictionaries",
        json={"native_lang": "en", "study_lang": "ru", "n_to_learn": 5},
    )
    assert r.status_code == 201
    words = authed_client.get(f"/dictionaries/{r.json()['id']}/words").json()
    assert len(words) == 10
    assert words[0]["word"] == "привет"
    assert words[0]["translation"] == "hello"


def test_create_dictionary_other_pair_no_seed(authed_client: TestClient):
    r = authed_client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "es", "n_to_learn": 5},
    )
    assert r.status_code == 201
    words = authed_client.get(f"/dictionaries/{r.json()['id']}/words").json()
    assert words == []


def test_create_dictionary_duplicate_409(authed_client: TestClient):
    payload = {"native_lang": "ru", "study_lang": "en", "n_to_learn": 5}
    authed_client.post("/dictionaries", json=payload)
    r = authed_client.post("/dictionaries", json=payload)
    assert r.status_code == 409


def test_batch_add_words(authed_client: TestClient):
    d = authed_client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "es", "n_to_learn": 2},
    ).json()
    words = [{"word": f"palabra{i}", "translation": f"слово{i}"} for i in range(10)]
    r = authed_client.post(f"/dictionaries/{d['id']}/words/batch", json={"words": words})
    assert r.status_code == 201
    assert len(r.json()) == 10


def test_start_session_too_few_words_400(authed_client: TestClient):
    d = authed_client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "es", "n_to_learn": 5},
    ).json()
    for i in range(3):
        authed_client.post(
            f"/dictionaries/{d['id']}/words",
            json={"word": f"w{i}", "translation": f"t{i}"},
        )
    r = authed_client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.new.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 3,
        },
    )
    assert r.status_code == 400


def test_study_new_session_and_learn(authed_client: TestClient):
    d = authed_client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 1},
    ).json()
    s = authed_client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.new.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 5,
        },
    )
    assert s.status_code == 200
    data = s.json()
    sid = data["session_id"]
    assert len(data["questions"]) == 5

    for q in data["questions"]:
        ans = q["options"][q["correct_index"]]
        r = authed_client.post(
            f"/study/sessions/{sid}/answer",
            json={"word_id": q["word_id"], "chosen": ans},
        )
        assert r.json()["is_correct"] is True

    res = authed_client.post(f"/study/sessions/{sid}/finish").json()
    assert res["total"] == 5
    assert res["correct"] == 5
    assert res["correct_pct"] == 100.0

    words = authed_client.get(f"/dictionaries/{d['id']}/words", params={"learned": "true"}).json()
    assert len(words) == 5
    assert all(w["correct_count"] == 1 for w in words)


def test_n_to_learn_threshold_marks_learned(authed_client: TestClient):
    d = authed_client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 2},
    ).json()

    s = authed_client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.new.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 10,
        },
    ).json()
    for q in s["questions"]:
        ans = q["options"][q["correct_index"]]
        authed_client.post(
            f"/study/sessions/{s['session_id']}/answer",
            json={"word_id": q["word_id"], "chosen": ans},
        )

    words = authed_client.get(f"/dictionaries/{d['id']}/words").json()
    assert all(not w["learned"] for w in words)
    assert all(w["correct_count"] == 1 for w in words)

    s2 = authed_client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.new.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 10,
        },
    ).json()
    for q in s2["questions"]:
        ans = q["options"][q["correct_index"]]
        authed_client.post(
            f"/study/sessions/{s2['session_id']}/answer",
            json={"word_id": q["word_id"], "chosen": ans},
        )

    words = authed_client.get(f"/dictionaries/{d['id']}/words").json()
    learned = [w for w in words if w["learned"]]
    assert len(learned) == 10
    assert all(w["correct_count"] >= 2 for w in learned)


def test_update_n_recomputes_learned(authed_client: TestClient):
    d = authed_client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 5},
    ).json()

    sid = authed_client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.new.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 1,
        },
    ).json()["session_id"]
    q = authed_client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.new.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 1,
        },
    ).json()["questions"][0]
    ans = q["options"][q["correct_index"]]
    authed_client.post(
        f"/study/sessions/{sid}/answer", json={"word_id": q["word_id"], "chosen": ans}
    )

    authed_client.patch(f"/dictionaries/{d['id']}", json={"n_to_learn": 1})
    words = authed_client.get(f"/dictionaries/{d['id']}/words").json()
    learned = [w for w in words if w["learned"]]
    assert any(w["correct_count"] == 1 for w in learned)


def test_review_mode_only_learned(authed_client: TestClient):
    d = authed_client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 1},
    ).json()
    s = authed_client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.new.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 3,
        },
    ).json()
    for q in s["questions"]:
        ans = q["options"][q["correct_index"]]
        authed_client.post(
            f"/study/sessions/{s['session_id']}/answer",
            json={"word_id": q["word_id"], "chosen": ans},
        )

    r = authed_client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.review.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 2,
        },
    )
    assert r.status_code == 200
    assert len(r.json()["questions"]) == 2

    r2 = authed_client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.review.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 10,
        },
    )
    assert r2.json()["questions"][0]["word_id"] in [q["word_id"] for q in s["questions"]]


def test_review_no_learned_400(authed_client: TestClient):
    d = authed_client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 5},
    ).json()
    r = authed_client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.review.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 5,
        },
    )
    assert r.status_code == 400


def test_stats_and_calendar(authed_client: TestClient):
    d = authed_client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 1},
    ).json()
    s = authed_client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.new.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 5,
        },
    ).json()
    for q in s["questions"]:
        ans = q["options"][q["correct_index"]]
        authed_client.post(
            f"/study/sessions/{s['session_id']}/answer",
            json={"word_id": q["word_id"], "chosen": ans},
        )
    authed_client.post(f"/study/sessions/{s['session_id']}/finish")

    from datetime import date

    year = date.today().year
    stats = authed_client.get("/stats", params={"dictionary_id": d["id"]}).json()
    assert stats["total_words"] == 10
    assert stats["learned_words"] == 5
    assert stats["learning_words"] == 5

    cal = authed_client.get(
        "/stats/calendar", params={"dictionary_id": d["id"], "year": year}
    ).json()
    assert len(cal) >= 1
    assert sum(c["count"] for c in cal) == 1


def test_languages_list(client: TestClient):
    r = client.get("/dictionaries/languages/list", params={"ui_locale": "en"})
    assert r.status_code == 200
    codes = [item["code"] for item in r.json()]
    assert "en" in codes
    names = {item["code"]: item["name"] for item in r.json()}
    assert names["ru"] == "Russian"


# --- LLM ---


def test_llm_settings_save_and_get(authed_client: TestClient):
    r = authed_client.get("/llm/settings")
    assert r.status_code == 200
    assert r.json() is None

    authed_client.put(
        "/llm/settings",
        json={
            "base_url": "https://api.example.com/v1/chat/completions",
            "api_key": "sk-test",
            "model": "gpt-4o",
        },
    )

    r = authed_client.get("/llm/settings")
    data = r.json()
    assert data["base_url"] == "https://api.example.com/v1/chat/completions"
    assert data["model"] == "gpt-4o"
    assert data["has_key"] is True


def test_llm_translate_not_configured(authed_client: TestClient):
    d = authed_client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 1},
    ).json()
    r = authed_client.post("/llm/translate", json={"text": "hello", "dictionary_id": d["id"]})
    assert r.status_code == 400


def test_llm_translate_with_mock(authed_client: TestClient, httpx_mock):
    d = authed_client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 1},
    ).json()

    authed_client.put(
        "/llm/settings",
        json={
            "base_url": "https://api.example.com/v1/chat/completions",
            "api_key": "sk-test",
            "model": "gpt-4o",
        },
    )

    httpx_mock.add_response(
        url="https://api.example.com/v1/chat/completions",
        json={
            "choices": [{"message": {"content": "привет"}}],
        },
    )

    r = authed_client.post("/llm/translate", json={"text": "hello", "dictionary_id": d["id"]})
    assert r.status_code == 200
    assert r.json()["translation"] == "привет"


def test_llm_models_with_mock(authed_client: TestClient, httpx_mock):
    httpx_mock.add_response(
        url="https://api.example.com/v1/models",
        json={"data": [{"id": "gpt-4o"}, {"id": "gpt-4o-mini"}]},
    )
    r = authed_client.post(
        "/llm/models",
        json={
            "base_url": "https://api.example.com/v1/chat/completions",
            "api_key": "sk-test",
        },
    )
    assert r.status_code == 200
    assert r.json()["models"] == ["gpt-4o", "gpt-4o-mini"]


# --- Library ---


def test_library_upload_and_read(authed_client: TestClient, httpx_mock):
    buf = _make_pdf()

    r = authed_client.post(
        "/library/books",
        files={"file": ("test.pdf", buf, "application/pdf")},
    )
    assert r.status_code == 201
    book = r.json()
    assert book["title"] == "test"
    assert book["total_pages"] == 1

    r = authed_client.get("/library/books")
    assert len(r.json()) == 1

    r = authed_client.get(f"/library/books/{book['id']}", params={"page": 0})
    assert r.status_code == 200
    assert "Hello world" in r.json()["page_text"]

    r = authed_client.patch(f"/library/books/{book['id']}", json={"last_page": 0})
    assert r.status_code == 200
    assert r.json()["last_page"] == 0


def test_library_unsupported_type(authed_client: TestClient):
    r = authed_client.post(
        "/library/books",
        files={"file": ("doc.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 400


def test_library_duplicate_filename_409(authed_client: TestClient):
    buf = _make_pdf()
    r = authed_client.post(
        "/library/books",
        files={"file": ("test.pdf", buf, "application/pdf")},
    )
    assert r.status_code == 201
    r = authed_client.post(
        "/library/books",
        files={"file": ("test.pdf", buf, "application/pdf")},
    )
    assert r.status_code == 409


def test_library_delete(authed_client: TestClient, httpx_mock):
    buf = _make_pdf()
    r = authed_client.post(
        "/library/books",
        files={"file": ("test.pdf", buf, "application/pdf")},
    )
    book_id = r.json()["id"]
    r = authed_client.delete(f"/library/books/{book_id}")
    assert r.status_code == 204
    assert len(authed_client.get("/library/books").json()) == 0


def test_library_isolation(client: TestClient, httpx_mock):
    client.post("/auth/register", json={"username": "u1", "password": "pw"})
    r1 = client.post("/auth/login", json={"username": "u1", "password": "pw"})
    h1 = {"Authorization": f"Bearer {r1.json()['access_token']}"}

    client.post("/auth/register", json={"username": "u2", "password": "pw"})
    r2 = client.post("/auth/login", json={"username": "u2", "password": "pw"})
    h2 = {"Authorization": f"Bearer {r2.json()['access_token']}"}

    buf = _make_pdf()
    r = client.post(
        "/library/books",
        files={"file": ("test.pdf", buf, "application/pdf")},
        headers=h1,
    )
    book_id = r.json()["id"]

    r = client.get(f"/library/books/{book_id}", headers=h2)
    assert r.status_code == 404


def _make_pdf() -> bytes:
    from io import BytesIO

    from reportlab.pdfgen import canvas

    buf = BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, "Hello world this is page one")
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
