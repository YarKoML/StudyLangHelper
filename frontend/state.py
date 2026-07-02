"""Хелперы для session_state Streamlit."""

import streamlit as st


def init_state(key: str, default) -> None:
    if key not in st.session_state:
        st.session_state[key] = default


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