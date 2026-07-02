"""Страница Библиотека: чтение PDF-книг с переводом выделенных слов через LLM."""

import contextlib

import streamlit as st

from frontend import api_client
from frontend.i18n import t
from frontend.state import ensure_auth_state, ensure_library_state, reset_library_state

ensure_auth_state()
ensure_library_state()
locale = st.session_state["ui_locale"]

st.title(t("library_title", locale))

selected_book_id = st.session_state.get("lib_selected_book")

if selected_book_id is None:
    try:
        books = api_client.list_books()
    except Exception:
        st.error(t("api_error", locale))
        st.stop()

    if not books:
        st.info(t("no_books", locale))
        st.stop()

    for b in books:
        with st.container(border=True):
            c1, c2, c3 = st.columns([5, 1, 1])
            c1.write(
                f"**{b['title']}**  \n{b['source_filename']} · "
                f"{b['total_pages']} {t('page', locale).lower()}"
            )
            if c2.button(t("read_book", locale), key=f"read_{b['id']}"):
                st.session_state["lib_selected_book"] = b["id"]
                st.session_state["lib_current_page"] = b.get("last_page", 0)
                st.rerun()
            if c3.button(t("delete", locale), key=f"del_book_{b['id']}"):
                api_client.delete_book(b["id"])
                st.toast(t("book_deleted", locale), icon="🗑️")
                st.rerun()
            progress = (b["last_page"] + 1) / b["total_pages"] if b["total_pages"] > 0 else 0
            pct = int(progress * 100)
            progress_text = (
                f"{t('reading_progress', locale)}: {b['last_page'] + 1}/{b['total_pages']} · {pct}%"
            )
            st.progress(progress, text=progress_text)
    st.stop()

# --- Режим чтения ---
book_id = selected_book_id
page_num = st.session_state.get("lib_current_page", 0)

try:
    page_data = api_client.get_book_page(book_id, page_num)
except Exception as e:
    st.error(f"{t('error', locale)}: {e}")
    if st.button("←", key="back_from_error"):
        reset_library_state()
        st.rerun()
    st.stop()

col_read, col_translate = st.columns([3, 1])

with col_read:
    if st.button("←", key="back_to_list"):
        reset_library_state()
        st.rerun()

    st.subheader(f"{page_data['title']}")

    nav_prev, nav_info, nav_next = st.columns([1, 4, 1])
    with nav_prev:
        if st.button("←", key="prev_page_btn", disabled=page_num == 0):
            st.session_state["lib_current_page"] = page_num - 1
            with contextlib.suppress(Exception):
                api_client.update_book_position(book_id, page_num - 1)
            st.rerun()
    with nav_info:
        st.write(
            f"{t('page', locale)} **{page_num + 1}** {t('of', locale)} {page_data['total_pages']}"
        )
    with nav_next:
        if st.button(
            "→",
            key="next_page_btn",
            disabled=page_num >= page_data["total_pages"] - 1,
        ):
            st.session_state["lib_current_page"] = page_num + 1
            with contextlib.suppress(Exception):
                api_client.update_book_position(book_id, page_num + 1)
            st.rerun()

    read_progress = (page_num + 1) / page_data["total_pages"] if page_data["total_pages"] > 0 else 0
    st.progress(read_progress, text=f"{int(read_progress * 100)}%")

    st.divider()
    st.markdown(page_data["page_text"] or "—")

with col_translate:
    st.subheader(t("translation", locale))

    translate_input = st.text_input(
        t("translate_placeholder", locale),
        value=st.session_state.get("lib_translate_text", ""),
        key="lib_translate_text_input",
    )

    if st.button(t("translate_btn", locale), key="translate_btn"):
        if translate_input.strip():
            try:
                dicts = api_client.list_dictionaries(locale)
            except Exception:
                dicts = []
            if not dicts:
                st.warning(t("no_dicts", locale))
            else:
                try:
                    result = api_client.llm_translate(translate_input.strip(), dicts[0]["id"])
                    st.session_state["lib_last_translation"] = result["translation"]
                except Exception as e:
                    detail = ""
                    try:
                        import httpx

                        if isinstance(e, httpx.HTTPStatusError):
                            detail = e.response.json().get("detail", str(e))
                    except Exception:
                        detail = str(e)
                    st.error(f"{t('error', locale)}: {detail}")
        else:
            st.session_state["lib_last_translation"] = None

    translation = st.session_state.get("lib_last_translation")
    if translation:
        st.info(f"**{t('translation_result', locale)}:**\n\n{translation}")

        try:
            dicts = api_client.list_dictionaries(locale)
        except Exception:
            dicts = []

        if dicts:
            dict_options = {d["id"]: d["name"] for d in dicts}
            selected_dict_id = st.selectbox(
                t("select_dict", locale),
                options=list(dict_options.keys()),
                format_func=lambda x: dict_options[x],
                key="lib_dict_select",
            )
            if st.button(t("add_to_dict", locale), key="add_to_dict_btn"):
                try:
                    api_client.create_word(
                        selected_dict_id,
                        translate_input.strip(),
                        translation.strip(),
                    )
                    st.toast(t("added_to_dict", locale), icon="✅")
                except Exception as e:
                    st.error(f"{t('error', locale)}: {e}")
        else:
            st.info(t("no_dicts", locale))
