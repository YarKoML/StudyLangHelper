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


def test_create_dictionary_ru_en_seeds_10_words(client: TestClient):
    r = client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 3},
    )
    assert r.status_code == 201
    d = r.json()
    assert d["native_lang"] == "ru"
    assert d["study_lang"] == "en"
    assert d["name"] == "Русский → Английский"

    words = client.get(f"/dictionaries/{d['id']}/words").json()
    assert len(words) == 10
    assert all(w["correct_count"] == 0 for w in words)
    assert all(not w["learned"] for w in words)
    assert words[0]["word"] == "hello"
    assert words[0]["translation"] == "привет"


def test_create_dictionary_en_ru_seeds_reversed(client: TestClient):
    r = client.post(
        "/dictionaries",
        json={"native_lang": "en", "study_lang": "ru", "n_to_learn": 5},
    )
    assert r.status_code == 201
    words = client.get(f"/dictionaries/{r.json()['id']}/words").json()
    assert len(words) == 10
    assert words[0]["word"] == "привет"
    assert words[0]["translation"] == "hello"


def test_create_dictionary_other_pair_no_seed(client: TestClient):
    r = client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "es", "n_to_learn": 5},
    )
    assert r.status_code == 201
    words = client.get(f"/dictionaries/{r.json()['id']}/words").json()
    assert words == []


def test_create_dictionary_duplicate_409(client: TestClient):
    payload = {"native_lang": "ru", "study_lang": "en", "n_to_learn": 5}
    client.post("/dictionaries", json=payload)
    r = client.post("/dictionaries", json=payload)
    assert r.status_code == 409


def test_batch_add_words(client: TestClient):
    d = client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "es", "n_to_learn": 2},
    ).json()
    words = [{"word": f"palabra{i}", "translation": f"слово{i}"} for i in range(10)]
    r = client.post(f"/dictionaries/{d['id']}/words/batch", json={"words": words})
    assert r.status_code == 201
    assert len(r.json()) == 10


def test_start_session_too_few_words_400(client: TestClient):
    d = client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "es", "n_to_learn": 5},
    ).json()
    for i in range(3):
        client.post(
            f"/dictionaries/{d['id']}/words",
            json={"word": f"w{i}", "translation": f"t{i}"},
        )
    r = client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.new.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 3,
        },
    )
    assert r.status_code == 400


def test_study_new_session_and_learn(client: TestClient):
    d = client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 1},
    ).json()
    s = client.post(
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
        r = client.post(
            f"/study/sessions/{sid}/answer",
            json={"word_id": q["word_id"], "chosen": ans},
        )
        assert r.json()["is_correct"] is True

    res = client.post(f"/study/sessions/{sid}/finish").json()
    assert res["total"] == 5
    assert res["correct"] == 5
    assert res["correct_pct"] == 100.0

    words = client.get(f"/dictionaries/{d['id']}/words", params={"learned": "true"}).json()
    assert len(words) == 5
    assert all(w["correct_count"] == 1 for w in words)


def test_n_to_learn_threshold_marks_learned(client: TestClient):
    d = client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 2},
    ).json()

    s = client.post(
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
        client.post(
            f"/study/sessions/{s['session_id']}/answer",
            json={"word_id": q["word_id"], "chosen": ans},
        )

    words = client.get(f"/dictionaries/{d['id']}/words").json()
    assert all(not w["learned"] for w in words)
    assert all(w["correct_count"] == 1 for w in words)

    s2 = client.post(
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
        client.post(
            f"/study/sessions/{s2['session_id']}/answer",
            json={"word_id": q["word_id"], "chosen": ans},
        )

    words = client.get(f"/dictionaries/{d['id']}/words").json()
    learned = [w for w in words if w["learned"]]
    assert len(learned) == 10
    assert all(w["correct_count"] >= 2 for w in learned)


def test_update_n_recomputes_learned(client: TestClient):
    d = client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 5},
    ).json()

    sid = client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.new.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 1,
        },
    ).json()["session_id"]
    q = client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.new.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 1,
        },
    ).json()["questions"][0]
    ans = q["options"][q["correct_index"]]
    client.post(f"/study/sessions/{sid}/answer", json={"word_id": q["word_id"], "chosen": ans})

    client.patch(f"/dictionaries/{d['id']}", json={"n_to_learn": 1})
    words = client.get(f"/dictionaries/{d['id']}/words").json()
    learned = [w for w in words if w["learned"]]
    assert any(w["correct_count"] == 1 for w in learned)


def test_review_mode_only_learned(client: TestClient):
    d = client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 1},
    ).json()
    s = client.post(
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
        client.post(
            f"/study/sessions/{s['session_id']}/answer",
            json={"word_id": q["word_id"], "chosen": ans},
        )

    r = client.post(
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

    r2 = client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.review.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 10,
        },
    )
    assert r2.json()["questions"][0]["word_id"] in [q["word_id"] for q in s["questions"]]


def test_review_no_learned_400(client: TestClient):
    d = client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 5},
    ).json()
    r = client.post(
        "/study/sessions",
        json={
            "dictionary_id": d["id"],
            "mode": StudyMode.review.value,
            "direction": StudyDirection.word_to_translation.value,
            "count": 5,
        },
    )
    assert r.status_code == 400


def test_stats_and_calendar(client: TestClient):
    d = client.post(
        "/dictionaries",
        json={"native_lang": "ru", "study_lang": "en", "n_to_learn": 1},
    ).json()
    s = client.post(
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
        client.post(
            f"/study/sessions/{s['session_id']}/answer",
            json={"word_id": q["word_id"], "chosen": ans},
        )
    client.post(f"/study/sessions/{s['session_id']}/finish")

    from datetime import date

    year = date.today().year
    stats = client.get("/stats", params={"dictionary_id": d["id"]}).json()
    assert stats["total_words"] == 10
    assert stats["learned_words"] == 5
    assert stats["learning_words"] == 5

    cal = client.get("/stats/calendar", params={"dictionary_id": d["id"], "year": year}).json()
    assert len(cal) >= 1
    assert sum(c["count"] for c in cal) == 1


def test_languages_list(client: TestClient):
    r = client.get("/dictionaries/languages/list", params={"ui_locale": "en"})
    assert r.status_code == 200
    codes = [item["code"] for item in r.json()]
    assert "en" in codes
    names = {item["code"]: item["name"] for item in r.json()}
    assert names["ru"] == "Russian"