"""Страница настроек: словари, слова, порог N, LLM."""

import streamlit as st

from frontend import api_client
from frontend.i18n import t
from frontend.state import ensure_auth_state

ensure_auth_state()
locale = st.session_state["ui_locale"]

st.title(t("settings_title", locale))

try:
    dicts = api_client.list_dictionaries(locale)
    languages = api_client.list_languages(locale)
except Exception:
    st.error(t("api_error", locale))
    st.stop()

lang_code_to_name = {lang["code"]: lang["name"] for lang in languages}

tab_dicts, tab_words, tab_n, tab_llm = st.tabs(
    [
        t("tab_dictionaries", locale),
        t("tab_words", locale),
        t("tab_threshold", locale),
        t("tab_llm", locale),
    ]
)


with tab_dicts:
    st.subheader(t("create_dict", locale))
    with st.form("create_dict_form"):
        native = st.selectbox(
            t("native_lang", locale),
            options=[lang["code"] for lang in languages],
            format_func=lambda c: lang_code_to_name.get(c, c),
        )
        study = st.selectbox(
            t("study_lang", locale),
            options=[lang["code"] for lang in languages],
            format_func=lambda c: lang_code_to_name.get(c, c),
            index=1 if len(languages) > 1 else 0,
        )
        n_to_learn = st.number_input(t("n_to_learn", locale), min_value=1, max_value=100, value=5)
        submitted = st.form_submit_button(t("create_dict", locale))

    if submitted:
        if native == study:
            st.error("native != study" if locale == "en" else "Языки должны различаться")
        else:
            try:
                api_client.create_dictionary(native, study, int(n_to_learn), locale)
                st.rerun()
            except Exception as e:
                detail = ""
                try:
                    import httpx

                    if isinstance(e, httpx.HTTPStatusError):
                        detail = e.response.json().get("detail", str(e))
                except Exception:
                    detail = str(e)
                st.error(f"{t('error', locale)}: {detail}")

    st.divider()
    st.subheader(t("existing_dicts", locale))
    for d in dicts:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.write(f"**{d['name']}**  \nN = {d['n_to_learn']}")
            if c2.button(t("delete", locale), key=f"del_dict_{d['id']}"):
                api_client.delete_dictionary(d["id"])
                st.rerun()

    if not dicts:
        st.info(t("no_dicts", locale))

with tab_words:
    if not dicts:
        st.info(t("no_dicts", locale))
    else:
        dict_options = {d["id"]: d["name"] for d in dicts}
        selected_id = st.selectbox(
            t("study_dict", locale),
            options=list(dict_options.keys()),
            format_func=lambda x: dict_options[x],
            key="words_dict_select",
        )

        with st.form("add_word_form", clear_on_submit=True):
            new_word = st.text_input(t("word", locale))
            new_tr = st.text_input(t("translation", locale))
            add_btn = st.form_submit_button(t("add", locale))
        if add_btn and new_word and new_tr:
            try:
                api_client.create_word(selected_id, new_word.strip(), new_tr.strip())
                st.toast(t("word_added", locale), icon="✅")
            except Exception as e:
                st.error(f"{t('error', locale)}: {e}")

        filter_opt = st.radio(
            t("filter_all", locale),
            options=["all", "true", "false"],
            format_func=lambda x: {
                "all": t("filter_all", locale),
                "true": t("filter_learned", locale),
                "false": t("filter_learning", locale),
            }[x],
            horizontal=True,
            key="words_filter",
            label_visibility="collapsed",
        )

        try:
            words = api_client.list_words(selected_id, filter_opt)
        except Exception:
            words = []

        if words:
            rows = []
            for w in words:
                status = (
                    t("word_status_learned", locale)
                    if w["learned"]
                    else t("word_status_learning", locale)
                )
                rows.append(
                    {
                        t("word", locale): w["word"],
                        t("translation", locale): w["translation"],
                        t("correct", locale): w["correct_count"],
                        "": status,
                    }
                )
            st.dataframe(rows, width="stretch", hide_index=True)

            delete_word_id = st.selectbox(
                f"{t('delete', locale)}: {t('word', locale)}",
                options=[w["id"] for w in words],
                format_func=lambda wid: next(
                    f"{w['word']} — {w['translation']}" for w in words if w["id"] == wid
                ),
                key="word_del_select",
            )
            if st.button(t("delete", locale), key="del_word_btn"):
                api_client.delete_word(delete_word_id)
                st.success(t("word_deleted", locale))
                st.rerun()
        else:
            st.info("—" if locale == "en" else "Слов нет")

with tab_n:
    if not dicts:
        st.info(t("no_dicts", locale))
    else:
        for d in dicts:
            with st.container(border=True):
                st.write(f"**{d['name']}**")
                new_n = st.number_input(
                    t("n_to_learn", locale),
                    min_value=1,
                    max_value=100,
                    value=d["n_to_learn"],
                    key=f"n_input_{d['id']}",
                )
                if st.button(t("save_n", locale), key=f"save_n_{d['id']}"):
                    try:
                        api_client.update_dictionary(d["id"], int(new_n), locale)
                        st.success(t("n_saved", locale))
                    except Exception as e:
                        st.error(f"{t('error', locale)}: {e}")

with tab_llm:
    st.subheader(t("llm_settings_title", locale))

    try:
        current = api_client.get_llm_settings()
    except Exception:
        current = None

    base_url_default = current.get("base_url", "") if current else ""
    model_default = current.get("model", "") if current else ""

    if current and current.get("has_key"):
        st.info(f"{t('has_key', locale)} ✓")

    base_url = st.text_input(
        t("base_url", locale),
        value=base_url_default,
        placeholder="https://api.openai.com/v1/chat/completions",
        key="llm_base_url",
    )
    api_key_input = st.text_input(
        t("api_key", locale),
        type="password",
        placeholder="sk-..." if not current else "•••••••• (введите новый, чтобы заменить)",
        key="llm_api_key",
    )

    if "llm_loaded_models" not in st.session_state:
        st.session_state["llm_loaded_models"] = []
    if "llm_selected_model" not in st.session_state:
        st.session_state["llm_selected_model"] = model_default

    col_load, _ = st.columns([1, 3])
    with col_load:
        if st.button(t("load_models", locale), key="load_models_btn"):
            if not base_url or not api_key_input:
                st.error(t("error", locale))
            else:
                try:
                    models = api_client.list_llm_models(base_url.strip(), api_key_input.strip())
                    st.session_state["llm_loaded_models"] = models
                    if models:
                        st.toast(t("models_loaded", locale), icon="✅")
                    else:
                        st.warning(t("no_models", locale))
                except Exception as e:
                    detail = ""
                    try:
                        import httpx

                        if isinstance(e, httpx.HTTPStatusError):
                            detail = e.response.json().get("detail", str(e))
                    except Exception:
                        detail = str(e)
                    st.error(f"{t('error', locale)}: {detail}")

    model_options = st.session_state["llm_loaded_models"] or (
        [model_default] if model_default else []
    )
    if model_options:
        current_idx = (
            model_options.index(st.session_state["llm_selected_model"])
            if st.session_state["llm_selected_model"] in model_options
            else 0
        )
        selected_model = st.selectbox(
            t("select_model", locale),
            options=model_options,
            index=current_idx,
            key="llm_selected_model",
        )

    if st.button(t("save_llm", locale), key="save_llm_btn"):
        if not base_url or not api_key_input or not st.session_state.get("llm_selected_model"):
            st.error(t("error", locale))
        else:
            try:
                api_client.save_llm_settings(
                    base_url.strip(),
                    api_key_input.strip(),
                    st.session_state["llm_selected_model"],
                )
                st.success(t("llm_saved", locale))
                st.session_state["llm_loaded_models"] = []
            except Exception as e:
                detail = ""
                try:
                    import httpx

                    if isinstance(e, httpx.HTTPStatusError):
                        detail = e.response.json().get("detail", str(e))
                except Exception:
                    detail = str(e)
                st.error(f"{t('error', locale)}: {detail}")
