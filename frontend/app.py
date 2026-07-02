"""Entrypoint StudyLangHelper — Streamlit multipage app."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from frontend.i18n import t

st.set_page_config(page_title="StudyLangHelper", layout="wide")

if "ui_locale" not in st.session_state:
    st.session_state["ui_locale"] = "ru"

locale = st.session_state["ui_locale"]

pg = st.navigation(
    [
        st.Page(
            "pages/home.py",
            title=t("nav_home", locale),
            url_path="home",
            default=True,
        ),
        st.Page("pages/cards.py", title=t("nav_cards", locale), url_path="cards"),
        st.Page("pages/settings.py", title=t("nav_settings", locale), url_path="settings"),
    ]
)

with st.sidebar:
    st.title(t("app_title", locale))
    ui_lang = st.selectbox(
        t("ui_language", locale),
        options=["ru", "en"],
        format_func=lambda x: "Русский" if x == "ru" else "English",
        key="ui_locale",
    )
    if ui_lang != locale:
        st.rerun()

pg.run()
