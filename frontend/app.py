"""Entrypoint StudyLangHelper — Streamlit multipage app."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from frontend import api_client
from frontend.i18n import t
from frontend.state import ensure_auth_state

st.set_page_config(page_title="StudyLangHelper", layout="wide")

ensure_auth_state()

if "ui_locale" not in st.session_state:
    st.session_state["ui_locale"] = "ru"

locale = st.session_state["ui_locale"]

logged_in = st.session_state.get("auth_token") is not None

if logged_in:
    pg = st.navigation(
        [
            st.Page(
                "pages/home.py",
                title=t("nav_home", locale),
                url_path="home",
                default=True,
            ),
            st.Page("pages/cards.py", title=t("nav_cards", locale), url_path="cards"),
            st.Page("pages/upload.py", title=t("nav_upload", locale), url_path="upload"),
            st.Page("pages/library.py", title=t("nav_library", locale), url_path="library"),
            st.Page("pages/settings.py", title=t("nav_settings", locale), url_path="settings"),
        ]
    )
    with st.sidebar:
        st.title(t("app_title", locale))
        user = st.session_state.get("auth_user")
        if user:
            st.write(f"{t('welcome', locale)}, **{user['username']}**")
        ui_lang = st.selectbox(
            t("ui_language", locale),
            options=["ru", "en"],
            format_func=lambda x: "Русский" if x == "ru" else "English",
            key="ui_locale",
        )
        if ui_lang != locale:
            st.rerun()
        st.divider()
        if st.button(t("logout", locale)):
            st.session_state["auth_token"] = None
            st.session_state["auth_user"] = None
            api_client.clear_cache()
            st.rerun()
    pg.run()
else:
    pg = st.navigation(
        [
            st.Page(
                "pages/login.py",
                title=t("login_title", locale),
                url_path="login",
                default=True,
            ),
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
