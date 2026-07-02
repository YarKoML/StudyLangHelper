"""Страница карточек: режимы, сессия, результаты."""

import streamlit as st

from frontend import api_client
from frontend.i18n import t
from frontend.state import ensure_cards_state, reset_cards_state

locale = st.session_state["ui_locale"]
ensure_cards_state()

st.title(t("cards_title", locale))

try:
    dicts = api_client.list_dictionaries(locale)
except Exception:
    st.error(t("api_error", locale))
    st.stop()

if not dicts:
    st.info(t("no_dicts", locale))
    st.stop()

dict_id = st.session_state.get("dict_id") or dicts[0]["id"]
st.session_state["dict_id"] = dict_id

if st.session_state["cards_finished"] and st.session_state["cards_result"]:
    res = st.session_state["cards_result"]
    st.subheader(t("results_title", locale))
    c1, c2 = st.columns(2)
    c1.metric(t("correct_pct", locale), f"{res['correct_pct']}%")
    c2.metric(t("wrong_pct", locale), f"{res['wrong_pct']}%")
    st.progress(res["correct_pct"] / 100)
    if st.button(t("back_to_setup", locale)):
        reset_cards_state()
        st.rerun()
    st.stop()

if st.session_state["cards_session_id"] is None:
    with st.form("cards_setup"):
        mode = st.radio(
            t("mode", locale),
            options=["review", "new"],
            format_func=lambda x: (
                t("mode_review", locale) if x == "review" else t("mode_new", locale)
            ),
        )
        direction = st.selectbox(
            t("direction", locale),
            options=["word_to_translation", "translation_to_word"],
            format_func=lambda x: (
                t("dir_word_to_translation", locale)
                if x == "word_to_translation"
                else t("dir_translation_to_word", locale)
            ),
        )
        count = st.number_input(t("count", locale), min_value=1, max_value=50, value=10, step=1)
        submitted = st.form_submit_button(t("start", locale))

    if submitted:
        try:
            data = api_client.start_session(dict_id, mode, direction, int(count))
        except Exception as e:
            detail = ""
            try:
                import httpx

                if isinstance(e, httpx.HTTPStatusError):
                    detail = e.response.json().get("detail", "")
            except Exception:
                pass
            st.error(f"{t('session_error', locale)}: {detail}")
            st.stop()
        st.session_state["cards_session_id"] = data["session_id"]
        st.session_state["cards_questions"] = data["questions"]
        st.session_state["cards_index"] = 0
        st.session_state["cards_correct"] = 0
        st.session_state["cards_wrong"] = 0
        st.session_state["cards_answered"] = False
        st.session_state["cards_last_result"] = None
        st.rerun()
    st.stop()


questions = st.session_state["cards_questions"]
i = st.session_state["cards_index"]

if i >= len(questions):
    result = api_client.finish_session(st.session_state["cards_session_id"])
    st.session_state["cards_result"] = result
    st.session_state["cards_finished"] = True
    st.rerun()

q = questions[i]
st.subheader(f"{i + 1} / {len(questions)}")
st.markdown(f"### {q['prompt']}")

if st.session_state["cards_answered"]:
    res = st.session_state["cards_last_result"]
    if res["is_correct"]:
        st.success(t("correct", locale))
    else:
        st.error(
            f"{t('wrong', locale)} {t('wrong_prefix', locale)} **{res['correct_translation']}**"
        )

    if st.button(t("next", locale)):
        st.session_state["cards_index"] = i + 1
        st.session_state["cards_answered"] = False
        st.session_state["cards_last_result"] = None
        st.rerun()
    st.stop()

cols = st.columns(2)
positions = [0, 1, 2, 3]
for idx, opt in enumerate(q["options"]):
    col = cols[idx % 2]
    if col.button(opt, key=f"opt_{i}_{idx}", width="stretch"):
        result = api_client.submit_answer(st.session_state["cards_session_id"], q["word_id"], opt)
        if result["is_correct"]:
            st.session_state["cards_correct"] += 1
        else:
            st.session_state["cards_wrong"] += 1
        st.session_state["cards_answered"] = True
        st.session_state["cards_last_result"] = result
        st.rerun()
