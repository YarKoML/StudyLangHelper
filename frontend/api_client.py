"""HTTP-клиент к backend FastAPI с кэшированием Streamlit."""

import httpx
import streamlit as st

from frontend.config import API_BASE_URL


@st.cache_data(ttl=60)
def list_dictionaries(ui_locale: str = "ru") -> list[dict]:
    r = httpx.get(f"{API_BASE_URL}/dictionaries", params={"ui_locale": ui_locale}, timeout=5)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=60)
def get_dictionary(dict_id: int, ui_locale: str = "ru") -> dict:
    r = httpx.get(
        f"{API_BASE_URL}/dictionaries/{dict_id}",
        params={"ui_locale": ui_locale},
        timeout=5,
    )
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=60)
def list_words(dict_id: int, learned: str = "all") -> list[dict]:
    r = httpx.get(
        f"{API_BASE_URL}/dictionaries/{dict_id}/words", params={"learned": learned}, timeout=5
    )
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=300)
def list_languages(ui_locale: str = "ru") -> list[dict]:
    r = httpx.get(
        f"{API_BASE_URL}/dictionaries/languages/list", params={"ui_locale": ui_locale}, timeout=5
    )
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=30)
def get_stats(dict_id: int) -> dict:
    r = httpx.get(f"{API_BASE_URL}/stats", params={"dictionary_id": dict_id}, timeout=5)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=30)
def get_calendar(dict_id: int, year: int) -> list[dict]:
    r = httpx.get(
        f"{API_BASE_URL}/stats/calendar",
        params={"dictionary_id": dict_id, "year": year},
        timeout=5,
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
        timeout=5,
    )
    r.raise_for_status()
    clear_cache()
    return r.json()


def update_dictionary(dict_id: int, n_to_learn: int, ui_locale: str = "ru") -> dict:
    r = httpx.patch(
        f"{API_BASE_URL}/dictionaries/{dict_id}",
        json={"n_to_learn": n_to_learn},
        params={"ui_locale": ui_locale},
        timeout=5,
    )
    r.raise_for_status()
    clear_cache()
    return r.json()


def delete_dictionary(dict_id: int) -> None:
    httpx.delete(f"{API_BASE_URL}/dictionaries/{dict_id}", timeout=5)
    clear_cache()


def create_word(dict_id: int, word: str, translation: str) -> dict:
    r = httpx.post(
        f"{API_BASE_URL}/dictionaries/{dict_id}/words",
        json={"word": word, "translation": translation},
        timeout=5,
    )
    r.raise_for_status()
    clear_cache()
    return r.json()


def create_words_batch(dict_id: int, words: list[dict]) -> list[dict]:
    r = httpx.post(
        f"{API_BASE_URL}/dictionaries/{dict_id}/words/batch",
        json={"words": words},
        timeout=5,
    )
    r.raise_for_status()
    clear_cache()
    return r.json()


def delete_word(word_id: int) -> None:
    httpx.delete(f"{API_BASE_URL}/words/{word_id}", timeout=5)
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
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def submit_answer(session_id: int, word_id: int, chosen: str) -> dict:
    r = httpx.post(
        f"{API_BASE_URL}/study/sessions/{session_id}/answer",
        json={"word_id": word_id, "chosen": chosen},
        timeout=5,
    )
    r.raise_for_status()
    return r.json()


def finish_session(session_id: int) -> dict:
    r = httpx.post(f"{API_BASE_URL}/study/sessions/{session_id}/finish", timeout=5)
    r.raise_for_status()
    return r.json()
