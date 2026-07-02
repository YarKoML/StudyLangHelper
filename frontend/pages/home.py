"""Главная страница: календарь активности + статистика."""

import calendar
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


def _colors(is_dark: bool) -> list[str]:
    if is_dark:
        return ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    return ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]


def _level(count: int) -> int:
    if count <= 0:
        return 0
    if count == 1:
        return 1
    if count <= 3:
        return 2
    if count <= 5:
        return 3
    return 4


def _discrete_colorscale(colors: list[str]) -> list[list]:
    stops: list[list] = []
    n = len(colors)
    for i, c in enumerate(colors):
        lo = i / n
        hi = (i + 1) / n
        stops.append([lo, c])
        stops.append([hi, c])
    return stops


def _y_labels(loc: str) -> list[str]:
    if loc == "ru":
        return ["Пн", "", "Ср", "", "Пт", "", "Вс"]
    return ["Mon", "", "Wed", "", "Fri", "", "Sun"]


def _month_labels(year: int, loc: str) -> list[str]:
    if loc == "ru":
        return ["Янв", "Фев", "Мар", "Апр", "Май", "Июн",
                "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
    return [calendar.month_abbr[m] for m in range(1, 13)]


def _build_grid(counts: dict[str, int], year: int):
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    grid: list[list[int]] = [[] for _ in range(7)]
    offset = (start.weekday() + 1) % 7
    for _ in range(offset):
        grid[0].append(-1)
    cur = start
    while cur <= end:
        iso = cur.isoformat()
        count = counts.get(iso, 0)
        grid[(cur.weekday() + 1) % 7].append(count)
        cur = date.fromordinal(cur.toordinal() + 1)
    max_cols = max(len(row) for row in grid)
    for row in grid:
        while len(row) < max_cols:
            row.append(-1)
    return grid, max_cols


def _month_annotations(year: int, loc: str, max_cols: int) -> list[dict]:
    labels = _month_labels(year, loc)
    annotations: list[dict] = []
    cur = date(year, 1, 1)
    col = 0
    prev_month = 0
    month_start_col = 0
    while cur.year == year:
        m = cur.month
        if m != prev_month:
            if prev_month != 0:
                mid = (month_start_col + col) / 2 - 0.5
                annotations.append(dict(
                    x=mid, y=-0.7, xref="x", yref="y",
                    text=labels[prev_month - 1],
                    showarrow=False, font=dict(size=11),
                ))
            month_start_col = col
            prev_month = m
        if cur.weekday() == 6:
            col += 1
        cur = date.fromordinal(cur.toordinal() + 1)
    mid = (month_start_col + col) / 2 - 0.5
    annotations.append(dict(
        x=mid, y=-0.7, xref="x", yref="y",
        text=labels[prev_month - 1],
        showarrow=False, font=dict(size=11),
    ))
    return annotations


def _build_customdata(grid: list[list[int]], loc: str) -> list[list[str]]:
    sessions_word = "сессий" if loc == "ru" else "sessions"
    no_activity = "Нет активности" if loc == "ru" else "No activity"
    out: list[list[str]] = []
    for row in grid:
        out_row: list[str] = []
        for v in row:
            if v < 0:
                out_row.append("")
            elif v == 0:
                out_row.append(no_activity)
            else:
                out_row.append(f"{v} {sessions_word}")
        out.append(out_row)
    return out


def _legend_html(colors: list[str], loc: str) -> str:
    less = "Меньше" if loc == "ru" else "Less"
    more = "Больше" if loc == "ru" else "More"
    swatches = "".join(
        f'<span style="background:{c};width:12px;height:12px;'
        f'display:inline-block;border-radius:2px;"></span>'
        for c in colors
    )
    return (
        f'<div style="display:flex;align-items:center;gap:4px;'
        f'font-size:12px;color:inherit;margin-top:4px;">'
        f'<span>{less}</span>{swatches}<span>{more}</span></div>'
    )


theme_type = st.context.theme.type
is_dark = theme_type == "dark"
colors = _colors(is_dark)

year = date.today().year
try:
    cal = api_client.get_calendar(dict_id, year)
except Exception:
    cal = []

counts = {item["date"]: item["count"] for item in cal}

grid, max_cols = _build_grid(counts, year)
z = [[_level(v) if v >= 0 else -1 for v in row] for row in grid]
customdata = _build_customdata(grid, locale)
y_labels = _y_labels(locale)
annotations = _month_annotations(year, locale, max_cols)

fig = go.Figure(
    data=go.Heatmap(
        z=z,
        y=y_labels,
        x=list(range(max_cols)),
        colorscale=_discrete_colorscale(colors),
        zmin=0,
        zmax=4,
        xgap=2,
        ygap=2,
        showscale=False,
        hoverongaps=False,
        customdata=customdata,
        hovertemplate="%{customdata}<extra></extra>",
    )
)
fig.update_layout(
    annotations=annotations,
    margin=dict(l=30, r=20, t=30, b=10),
    height=280,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(size=11)),
    xaxis=dict(showgrid=False, showticklabels=False, side="top"),
)
st.plotly_chart(fig, use_container_width=True)
st.markdown(_legend_html(colors, locale), unsafe_allow_html=True)