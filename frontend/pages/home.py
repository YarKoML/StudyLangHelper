"""Главная страница: календарь активности + статистика."""

from datetime import date

import plotly.graph_objects as go
import streamlit as st

from frontend import api_client
from frontend.i18n import t
from frontend.state import init_state

init_state("ui_locale", "ru")
locale = st.session_state["ui_locale"]
init_state("dict_id", None)

st.title(t("home_title", locale))

try:
    dicts = api_client.list_dictionaries(locale)
except Exception:
    st.error(t("api_error", locale))
    st.stop()

if not dicts:
    st.info(t("no_dicts", locale))
    st.stop()

if st.session_state["dict_id"] is None:
    st.session_state["dict_id"] = dicts[0]["id"]
dict_id = st.session_state["dict_id"]

try:
    stats = api_client.get_stats(dict_id)
except Exception:
    st.error(t("api_error", locale))
    st.stop()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(t("stats_total", locale), stats["total_words"])
col2.metric(t("stats_learned", locale), stats["learned_words"])
col3.metric(t("stats_learning", locale), stats["learning_words"])
col4.metric(t("stats_learned_pct", locale), f"{stats['learned_pct']}%")
col5.metric(t("stats_streak", locale), stats["streak_days"])

st.subheader(t("activity_calendar", locale))

year = date.today().year
try:
    cal = api_client.get_calendar(dict_id, year)
except Exception:
    cal = []

counts = {item["date"]: item["count"] for item in cal}

start = date(year, 1, 1)
end = date(year, 12, 31)

weeks: list[list[int | None]] = []
labels_y: list[str] = []
labels_x: list[str] = []

first_dow = start.weekday()
grid: list[list[int | None]] = [[] for _ in range(7)]
cur = start
week_labels = []

offset = (first_dow + 1) % 7
for _ in range(offset):
    grid[0].append(None)

week_idx = 0
while cur <= end:
    iso = cur.isoformat()
    count = counts.get(iso, 0)
    grid[(cur.weekday() + 1) % 7].append(count)
    if cur.weekday() == 6:
        week_idx += 1
    cur = date.fromordinal(cur.toordinal() + 1)

max_cols = max(len(row) for row in grid)
for row in grid:
    while len(row) < max_cols:
        row.append(None)

z = grid
y_days = (
    ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    if locale == "ru"
    else ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
)

fig = go.Figure(
    data=go.Heatmap(
        z=z,
        y=y_days,
        x=[f"W{i + 1}" for i in range(max_cols)],
        colorscale=[[0, "#ebedf0"], [0.4, "#9be9a8"], [0.7, "#40c463"], [1, "#216e39"]],
        showscale=False,
        hoverongaps=False,
        hovertemplate="%{z} sessions<br><extra></extra>",
    )
)
fig.update_layout(
    margin=dict(l=20, r=20, t=10, b=10),
    height=220,
    yaxis=dict(autorange="reversed", showgrid=False),
    xaxis=dict(showgrid=False, showticklabels=False),
)
st.plotly_chart(fig, width="stretch")
