"""HTTP-клиент к backend FastAPI с кэшированием Streamlit."""

import httpx
import streamlit as st

from frontend.config import API_BASE_URL

TIMEOUT = 10


def _auth_headers() -> dict[str, str]:
    token = st.session_state.get("auth_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# --- Auth ---


def register(username: str, password: str) -> dict:
    r = httpx.post(
        f"{API_BASE_URL}/auth/register",
        json={"username": username, "password": password},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def login(username: str, password: str) -> dict:
    r = httpx.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": username, "password": password},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def get_me() -> dict:
    r = httpx.get(f"{API_BASE_URL}/auth/me", headers=_auth_headers(), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


# --- Dictionaries ---


@st.cache_data(ttl=60)
def list_dictionaries(ui_locale: str = "ru") -> list[dict]:
    r = httpx.get(
        f"{API_BASE_URL}/dictionaries",
        params={"ui_locale": ui_locale},
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=60)
def get_dictionary(dict_id: int, ui_locale: str = "ru") -> dict:
    r = httpx.get(
        f"{API_BASE_URL}/dictionaries/{dict_id}",
        params={"ui_locale": ui_locale},
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=60)
def list_words(dict_id: int, learned: str = "all") -> list[dict]:
    r = httpx.get(
        f"{API_BASE_URL}/dictionaries/{dict_id}/words",
        params={"learned": learned},
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=300)
def list_languages(ui_locale: str = "ru") -> list[dict]:
    r = httpx.get(
        f"{API_BASE_URL}/dictionaries/languages/list",
        params={"ui_locale": ui_locale},
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=30)
def get_stats(dict_id: int) -> dict:
    r = httpx.get(
        f"{API_BASE_URL}/stats",
        params={"dictionary_id": dict_id},
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=30)
def get_calendar(dict_id: int, year: int) -> list[dict]:
    r = httpx.get(
        f"{API_BASE_URL}/stats/calendar",
        params={"dictionary_id": dict_id, "year": year},
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def clear_cache():
    st.cache_data.clear()


def create_dictionary(
    native_lang: str, study_lang: str, n_to_learn: int, ui_locale: str = "ru"
) -> dict:
    r = httpx.post(
        f"{API_BASE_URL}/dictionaries",
        json={"native_lang": native_lang, "study_lang": study_lang, "n_to_learn": n_to_learn},
        params={"ui_locale": ui_locale},
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    clear_cache()
    return r.json()


def update_dictionary(dict_id: int, n_to_learn: int, ui_locale: str = "ru") -> dict:
    r = httpx.patch(
        f"{API_BASE_URL}/dictionaries/{dict_id}",
        json={"n_to_learn": n_to_learn},
        params={"ui_locale": ui_locale},
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    clear_cache()
    return r.json()


def delete_dictionary(dict_id: int) -> None:
    httpx.delete(f"{API_BASE_URL}/dictionaries/{dict_id}", headers=_auth_headers(), timeout=TIMEOUT)
    clear_cache()


def create_word(dict_id: int, word: str, translation: str) -> dict:
    r = httpx.post(
        f"{API_BASE_URL}/dictionaries/{dict_id}/words",
        json={"word": word, "translation": translation},
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    clear_cache()
    return r.json()


def create_words_batch(dict_id: int, words: list[dict]) -> list[dict]:
    r = httpx.post(
        f"{API_BASE_URL}/dictionaries/{dict_id}/words/batch",
        json={"words": words},
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    clear_cache()
    return r.json()


def delete_word(word_id: int) -> None:
    httpx.delete(f"{API_BASE_URL}/words/{word_id}", headers=_auth_headers(), timeout=TIMEOUT)
    clear_cache()


def start_session(dictionary_id: int, mode: str, direction: str, count: int) -> dict:
    r = httpx.post(
        f"{API_BASE_URL}/study/sessions",
        json={
            "dictionary_id": dictionary_id,
            "mode": mode,
            "direction": direction,
            "count": count,
        },
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def submit_answer(session_id: int, word_id: int, chosen: str) -> dict:
    r = httpx.post(
        f"{API_BASE_URL}/study/sessions/{session_id}/answer",
        json={"word_id": word_id, "chosen": chosen},
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def finish_session(session_id: int) -> dict:
    r = httpx.post(
        f"{API_BASE_URL}/study/sessions/{session_id}/finish",
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


# --- LLM ---


def get_llm_settings() -> dict | None:
    r = httpx.get(f"{API_BASE_URL}/llm/settings", headers=_auth_headers(), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def save_llm_settings(base_url: str, api_key: str, model: str) -> dict:
    r = httpx.put(
        f"{API_BASE_URL}/llm/settings",
        json={"base_url": base_url, "api_key": api_key, "model": model},
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def list_llm_models(base_url: str, api_key: str) -> list[str]:
    r = httpx.post(
        f"{API_BASE_URL}/llm/models",
        json={"base_url": base_url, "api_key": api_key},
        headers=_auth_headers(),
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["models"]


def llm_translate(text: str, dictionary_id: int) -> dict:
    r = httpx.post(
        f"{API_BASE_URL}/llm/translate",
        json={"text": text, "dictionary_id": dictionary_id},
        headers=_auth_headers(),
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


# --- Library ---


@st.cache_data(ttl=30)
def list_books() -> list[dict]:
    r = httpx.get(f"{API_BASE_URL}/library/books", headers=_auth_headers(), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def upload_book(file_bytes: bytes, filename: str) -> dict:
    files = {"file": (filename, file_bytes, "application/pdf")}
    r = httpx.post(
        f"{API_BASE_URL}/library/books",
        files=files,
        headers=_auth_headers(),
        timeout=60,
    )
    r.raise_for_status()
    clear_cache()
    return r.json()


def get_book_page(book_id: int, page: int) -> dict:
    r = httpx.get(
        f"{API_BASE_URL}/library/books/{book_id}",
        params={"page": page},
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def update_book_position(book_id: int, last_page: int) -> dict:
    r = httpx.patch(
        f"{API_BASE_URL}/library/books/{book_id}",
        json={"last_page": last_page},
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def delete_book(book_id: int) -> None:
    httpx.delete(
        f"{API_BASE_URL}/library/books/{book_id}",
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    clear_cache()
