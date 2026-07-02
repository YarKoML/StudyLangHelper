"""Страница загрузки книг (PDF)."""

import streamlit as st

from frontend import api_client
from frontend.i18n import t
from frontend.state import ensure_auth_state

ensure_auth_state()
locale = st.session_state["ui_locale"]

st.title(t("upload_title", locale))

uploaded = st.file_uploader(t("upload_book", locale), type=["pdf"], key="pdf_uploader")

if st.button(t("upload_btn", locale), key="upload_btn", type="primary"):
    if uploaded is not None:
        with st.status(t("uploading_status", locale), expanded=True) as status:
            st.write(t("uploading_sending", locale))
            try:
                api_client.upload_book(uploaded.getvalue(), uploaded.name)
                status.update(label=t("book_uploaded", locale), state="complete", expanded=False)
                del st.session_state["pdf_uploader"]
                st.toast(t("book_uploaded", locale), icon="✅")
                st.rerun()
            except Exception as e:
                status.update(label=t("error", locale), state="error")
                detail = ""
                try:
                    import httpx

                    if isinstance(e, httpx.HTTPStatusError):
                        detail = e.response.json().get("detail", str(e))
                except Exception:
                    detail = str(e)
                st.error(f"{t('error', locale)}: {detail}")
    else:
        st.warning(t("select_file", locale))
