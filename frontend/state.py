"""Хелперы для session_state Streamlit."""

import streamlit as st


def init_state(key: str, default) -> None:
    if key not in st.session_state:
        st.session_state[key] = default


def ensure_auth_state():
    init_state("auth_token", None)
    init_state("auth_user", None)


def ensure_cards_state():
    init_state("cards_session_id", None)
    init_state("cards_questions", [])
    init_state("cards_index", 0)
    init_state("cards_correct", 0)
    init_state("cards_wrong", 0)
    init_state("cards_answered", False)
    init_state("cards_last_result", None)
    init_state("cards_finished", False)
    init_state("cards_result", None)


def reset_cards_state():
    st.session_state["cards_session_id"] = None
    st.session_state["cards_questions"] = []
    st.session_state["cards_index"] = 0
    st.session_state["cards_correct"] = 0
    st.session_state["cards_wrong"] = 0
    st.session_state["cards_answered"] = False
    st.session_state["cards_last_result"] = None
    st.session_state["cards_finished"] = False
    st.session_state["cards_result"] = None


def ensure_library_state():
    init_state("lib_current_page", 0)
    init_state("lib_selected_book", None)
    init_state("lib_translate_text", "")
    init_state("lib_last_translation", None)


def reset_library_state():
    st.session_state["lib_current_page"] = 0
    st.session_state["lib_selected_book"] = None
    st.session_state["lib_translate_text"] = ""
    st.session_state["lib_last_translation"] = None
