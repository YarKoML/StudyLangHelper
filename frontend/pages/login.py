"""Страница входа/регистрации."""

import streamlit as st

from frontend import api_client
from frontend.i18n import t
from frontend.state import ensure_auth_state

ensure_auth_state()
locale = st.session_state["ui_locale"]

st.title(t("app_title", locale))

tab_login, tab_register = st.tabs([t("login_title", locale), t("register_title", locale)])

with tab_login:
    with st.form("login_form"):
        username = st.text_input(t("username", locale), key="login_username")
        password = st.text_input(t("password", locale), type="password", key="login_password")
        submitted = st.form_submit_button(t("login_btn", locale))

    if submitted:
        if not username or not password:
            st.error(t("login_error", locale))
            st.stop()
        try:
            data = api_client.login(username.strip(), password)
            st.session_state["auth_token"] = data["access_token"]
            st.session_state["auth_user"] = data["user"]
            st.toast(t("login_success", locale), icon="✅")
            st.rerun()
        except Exception as e:
            detail = ""
            try:
                import httpx

                if isinstance(e, httpx.HTTPStatusError):
                    detail = e.response.json().get("detail", str(e))
            except Exception:
                detail = str(e)
            st.error(f"{t('login_error', locale)}: {detail}")

with tab_register:
    with st.form("register_form"):
        username = st.text_input(t("username", locale), key="reg_username")
        password = st.text_input(t("password", locale), type="password", key="reg_password")
        submitted = st.form_submit_button(t("register_btn", locale))

    if submitted:
        if not username or not password:
            st.error(t("register_error", locale))
            st.stop()
        try:
            data = api_client.register(username.strip(), password)
            st.session_state["auth_token"] = data["access_token"]
            st.session_state["auth_user"] = data["user"]
            st.toast(t("register_success", locale), icon="✅")
            st.rerun()
        except Exception as e:
            detail = ""
            try:
                import httpx

                if isinstance(e, httpx.HTTPStatusError):
                    detail = e.response.json().get("detail", str(e))
            except Exception:
                detail = str(e)
            st.error(f"{t('register_error', locale)}: {detail}")
